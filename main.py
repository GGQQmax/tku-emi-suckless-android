import os
import sys
import json
import re
import ssl
import urllib.request
import requests

from emis_api.emis_api import EMISStudentAPI
from emis_api.emis_auth_module import Authenticator

# Storage paths configuration
def get_data_dir():
    # 1. Android internal writable directories
    for env_var in ['ANDROID_APP_PATH', 'ANDROID_PRIVATE']:
        val = os.environ.get(env_var)
        if val and os.path.isdir(val):
            return val
    # 2. android.storage if available
    try:
        from android.storage import app_storage_path
        val = app_storage_path()
        if val and os.path.isdir(val):
            return val
    except Exception:
        pass
    # 3. Fallback to app directory for desktop/local execution
    return os.path.dirname(os.path.abspath(__file__))

DATA_DIR = get_data_dir()
SESSION_FILE = os.path.join(DATA_DIR, ".env")
USERSTORAGE = os.path.join(DATA_DIR, ".userData")

AUTH = None
API = None

def get_storage_data(fileName: str):
    data = {}
    filepath = os.path.join(USERSTORAGE, fileName)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading storage {fileName}: {e}")
    return data

def save_storage_data(fileName: str, data):
    if not os.path.exists(USERSTORAGE):
        os.makedirs(USERSTORAGE, exist_ok=True)
    filepath = os.path.join(USERSTORAGE, fileName)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def normalize_schedule(schedule):
    normalized = []
    for item in schedule:
        parts = [p.strip() for p in item.split("/")]
        if len(parts) >= 3:
            day, periods, room = parts[:3]
            # Pad every period to 2 digits
            periods = ",".join(f"{int(p):02d}" for p in periods.split(","))
            # Normalize room spacing
            room = re.sub(r"([A-Z])\s+(\d+)", r"\1  \2", room)
            item = f"{day} / {periods} / {room}"
        normalized.append(item)
    return normalized


class UI_Api:
    API_MAP = {
        "student_info": (
            "student_info.json",
            "get_student_info",
        ),
        "study_progress": (
            "study_progress.json",
            "get_study_progress_info",
        ),
        "required_courses": (
            "requiredCourses.json",
            "get_required_courses_and_graduation_credits",
        ),
        "all_grades": (
            "AllGrades.json",
            "get_all_years_course_grades",
        ),
        "missing_required_courses": (
            "get_missing_required_courses.json",
            "get_missing_required_courses",
        ),
        "course_selection": (
            "get_course_selection_by_course_code.json",
            "get_course_selection_by_course_code",
        ),
        "get_courses_we_have_this_semester": (
            "courses.json",
            "get_courses_we_have_this_semester",
        )
    }

    @property
    def courses(self):
        return self.courses_we_have_this_semester() or []

    def _get_api(self):
        global AUTH, API
        if AUTH is None or API is None:
            self.auth_login()
        if API is None:
            raise RuntimeError("Authentication required")
        return API

    def _data(self, filename, api_method, withUpdate=False):
        if withUpdate:
            api = self._get_api()
            data = getattr(api, api_method)()
            save_storage_data(filename, data)
            return data

        return get_storage_data(filename)

    def progress_on_graduation(self):
        """
        Return overall graduation progress percentage.
        """
        data = self.get_score()
        total_required = data.get("total_required", 0)
        total_credit = data.get("total_credit", 0)
        if total_required == 0:
            return {"total_percent": 0}
        return {
            "total_percent": round(
                total_credit / total_required * 100,
                2
            )
        }

    def get_score(self):
        student_info = self.student_info() or {}
        department = student_info.get("department", "")

        AllGrades = self.all_years_course_grades()
        requiredCourses = self.required_courses_and_graduation_credits()

        if AllGrades is None or requiredCourses is None or not AllGrades:
            AllGrades = self.all_years_course_grades(withUpdate=True)
            requiredCourses = self.required_courses_and_graduation_credits(withUpdate=True)

        courses = AllGrades.get("courses", []) if isinstance(AllGrades, dict) else []

        # =========================
        # 必修
        # =========================
        requiredScore = 0
        for course in courses:
            if (
                course.get("status") == "passed"
                and course.get("requirement_type") == "必修Required"
            ):
                requiredScore += course.get("credits_up", 0)

        # =========================
        # 本系選修
        # =========================
        electiveScore = 0
        for course in courses:
            if (
                course.get("status") == "passed"
                and course.get("requirement_type") == "選修Elective"
                and department
                and department in course.get("specialization", "")
            ):
                electiveScore += course.get("credits_up", 0)

        # =========================
        # 其他選修
        # =========================
        otherElectiveScore = 0
        for course in courses:
            if (
                course.get("status") == "passed"
                and course.get("requirement_type") == "選修Elective"
                and (not department or department not in course.get("specialization", ""))
            ):
                otherElectiveScore += course.get("credits_up", 0)

        # =========================
        # 體育
        # 體育有學分，但是不計入畢業學分
        # =========================
        score_pe_class = 0
        for course in courses:
            if (
                course.get("status") == "passed"
                and "體育" in course.get("specialization", "")
            ):
                score_pe_class += course.get("credits_up", 0)

        # =========================
        # 畢業學分要求
        # =========================
        credits = (requiredCourses.get("credits", {})
                   if isinstance(requiredCourses, dict) and "credits" in requiredCourses
                   else {})

        total_credit = credits.get("total", 128)
        required = credits.get("required", 90)
        elective_min = credits.get("elective_min", 18)

        other_elective_min = total_credit - required - elective_min

        # AllGrades 的總學分包含體育，不計入畢業學分，扣掉
        total_earned = AllGrades.get("total_earned_credits", 0) if isinstance(AllGrades, dict) else 0
        real_credit = total_earned - score_pe_class

        return {
            "total_credit": real_credit,
            "required_credit": requiredScore,
            "elective_credit": electiveScore,
            "other_elective_credit": otherElectiveScore,
            "total_need": max(0, total_credit - real_credit),
            "required_need": max(0, required - requiredScore),
            "elective_need": max(0, elective_min - electiveScore),
            "other_elective_need": max(0, other_elective_min - otherElectiveScore),
            "total_required": total_credit,
            "required_total": required,
            "elective_total": elective_min,
            "other_elective_total": other_elective_min,
        }

    def update_all_user_data(self):
        self.student_info(withUpdate=True)
        self.all_years_course_grades(withUpdate=True)
        self.required_courses_and_graduation_credits(withUpdate=True)
        self.missing_required_courses(withUpdate=True)
        self.course_selection_by_course_code(withUpdate=True)
        self.courses_we_have_this_semester(withUpdate=True)
        return {"done": True}

    def student_info(self, withUpdate=False):
        return self._data(
            "student_info.json",
            "get_student_info",
            withUpdate
        )

    def study_progress_info(self, withUpdate=False):
        return self._data(
            "study_progress.json",
            "get_study_progress_info",
            withUpdate
        )

    def required_courses_and_graduation_credits(self, withUpdate=False):
        return self._data(
            "requiredCourses.json",
            "get_required_courses_and_graduation_credits",
            withUpdate
        )

    def all_years_course_grades(self, withUpdate=False):
        return self._data(
            "AllGrades.json",
            "get_all_years_course_grades",
            withUpdate
        )

    def missing_required_courses(self, withUpdate=False):
        return self._data(
            "get_missing_required_courses.json",
            "get_missing_required_courses",
            withUpdate
        )

    def course_selection_by_course_code(self, withUpdate=False):
        return self._data(
            "get_course_selection_by_course_code.json",
            "get_course_selection_by_course_code",
            withUpdate
        )

    def courses_we_have_this_semester(self, withUpdate=False):
        if withUpdate:
            url = "https://raw.githubusercontent.com/tkuitocc/azquerysucks/main/courses.json"
            try:
                courses_data = None
                try:
                    response = requests.get(url, timeout=15)
                    response.raise_for_status()
                    courses_data = response.json()
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
                    # Fallback without SSL verification if local certificates cannot be validated
                    response = requests.get(url, verify=False, timeout=15)
                    response.raise_for_status()
                    courses_data = response.json()
                except Exception:
                    # Fallback to urllib with SSL context handling
                    try:
                        ctx = ssl.create_default_context(cafile=requests.certs.where())
                    except Exception:
                        ctx = ssl.create_default_context()
                    try:
                        with urllib.request.urlopen(url, context=ctx, timeout=15) as res:
                            courses_data = json.loads(res.read().decode('utf-8'))
                    except Exception:
                        unverified_ctx = ssl._create_unverified_context()
                        with urllib.request.urlopen(url, context=unverified_ctx, timeout=15) as res:
                            courses_data = json.loads(res.read().decode('utf-8'))

                if courses_data is not None:
                    save_storage_data("courses.json", data=courses_data)
                    return courses_data
                return get_storage_data("courses.json") or {}
            except Exception as e:
                print(f"Error fetching courses: {e}")
                return get_storage_data("courses.json") or {}
        else:
            return get_storage_data("courses.json")

    def schedule_my_class(self, schedule_data=None):
        data = get_storage_data("my_class.json")
        if data is None or not isinstance(data, list):
            data = []

        if schedule_data is None:
            return data

        if isinstance(schedule_data, dict) and "options" in schedule_data:
            option = schedule_data.get("options")
            course_id = schedule_data.get("course_id")

            if option == "add" and course_id:
                modified_class = self.find_class_by_course_code(course_id)
                if modified_class:
                    data.append(modified_class)
            elif option == "remove" and course_id:
                data = [cls for cls in data if cls.get("course_id") != course_id]
            elif option == "clear":
                data = []
            elif option == "load":
                data = self.course_selection_by_course_code()
                if not isinstance(data, list):
                    data = []

            save_storage_data("my_class.json", data)
            return data
        else:
            return data

    def find_class_by_course_code(self, course_code):
        data = get_storage_data("courses.json")
        if not isinstance(data, list):
            return None

        for course in data:
            if course.get("seq") == course_code:
                return {
                    "course_id": course.get("seq", ""),
                    "dept": (
                        course.get("dept_block", "").split("－")[0]
                        if course.get("dept_block")
                        else ""
                    ),
                    "grade": course.get("grade", ""),
                    "course_name": course.get("title", "").strip(),
                    "course_code": course.get("seq", ""),
                    "credits": str(course.get("credits", "")),
                    "teachers": (
                        [course["teacher"]]
                        if course.get("teacher")
                        else []
                    ),
                    "schedule": normalize_schedule(course.get("times", [])),
                    "seat_numbers": [],
                }
        return None

    def search_courses(self, options=None):
        if not options:
            options = {}

        title = options.get("title", "").lower()
        times = options.get("times", "").replace(" ", "")
        required = options.get("required", "")
        dept = options.get("dept_block", "").lower()

        result = []
        for course in self.courses:
            if title and title not in course.get("title", "").lower():
                continue
            if required and course.get("required") != required:
                continue
            if dept and dept not in course.get("dept_block", "").lower():
                continue
            if times:
                course_time = "".join(course.get("times", [])).replace(" ", "")
                if times not in course_time:
                    continue
            result.append(course)
        return result

    def auth_login(self):
        global AUTH, API
        if not os.path.exists(SESSION_FILE):
            return None
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                username = data.get("username")
                password = data.get("password")
            if not username or not password:
                return None
            AUTH = Authenticator(username=username, password=password)
            if AUTH.perform_auth() is False:
                raise RuntimeError("Authentication failed")
            API = EMISStudentAPI(AUTH.session)
            return API
        except Exception as e:
            print(f"Auth login error: {e}")
            self.logout()
            return None

    def check_saved_session(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("loginPass") is True:
                        return {"logged_in": True, "username": data.get("username", "")}
            except Exception:
                pass
        return {"logged_in": False}

    def authenticate(self, username, password):
        global AUTH, API
        try:
            auth = Authenticator(username=username, password=password)
            if auth.perform_auth() is not False:
                AUTH = auth
                API = EMISStudentAPI(AUTH.session)
                session_data = {
                    "loginPass": True,
                    "username": username,
                    "password": password,
                }
                with open(SESSION_FILE, "w", encoding="utf-8") as f:
                    json.dump(session_data, f)
                return True
        except Exception as e:
            print(f"Authentication error: {e}")
        return False

    def logout(self):
        global AUTH, API
        AUTH = None
        API = None
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except Exception:
                pass
        return True


GUI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gui')

try:
    from flask import Flask, request, jsonify, send_from_directory
    HAVE_FLASK = True
except ImportError:
    HAVE_FLASK = False

try:
    from bottle import Bottle, request as bottle_request, response as bottle_response, static_file
    HAVE_BOTTLE = True
except ImportError:
    HAVE_BOTTLE = False


def create_app(api_instance=None):
    if api_instance is None:
        api_instance = UI_Api()

    if HAVE_FLASK:
        app = Flask(__name__, static_folder=GUI_DIR, static_url_path='')

        @app.route('/')
        def serve_index():
            return send_from_directory(GUI_DIR, 'index.html')

        @app.route('/<path:path>')
        def serve_static(path):
            return send_from_directory(GUI_DIR, path)

        @app.route('/api/check_saved_session', methods=['GET'])
        def api_check_saved_session():
            return jsonify(api_instance.check_saved_session())

        @app.route('/api/authenticate', methods=['POST'])
        def api_authenticate():
            data = request.get_json(silent=True) or {}
            username = data.get('username', '')
            password = data.get('password', '')
            return jsonify(api_instance.authenticate(username, password))

        @app.route('/api/logout', methods=['POST'])
        def api_logout():
            return jsonify(api_instance.logout())

        @app.route('/api/student_info', methods=['GET'])
        def api_student_info():
            with_update = request.args.get('withUpdate', 'false').lower() == 'true'
            return jsonify(api_instance.student_info(withUpdate=with_update))

        @app.route('/api/study_progress_info', methods=['GET'])
        def api_study_progress_info():
            with_update = request.args.get('withUpdate', 'false').lower() == 'true'
            return jsonify(api_instance.study_progress_info(withUpdate=with_update))

        @app.route('/api/required_courses_and_graduation_credits', methods=['GET'])
        def api_required_courses_and_graduation_credits():
            with_update = request.args.get('withUpdate', 'false').lower() == 'true'
            return jsonify(api_instance.required_courses_and_graduation_credits(withUpdate=with_update))

        @app.route('/api/all_years_course_grades', methods=['GET'])
        def api_all_years_course_grades():
            with_update = request.args.get('withUpdate', 'false').lower() == 'true'
            return jsonify(api_instance.all_years_course_grades(withUpdate=with_update))

        @app.route('/api/missing_required_courses', methods=['GET'])
        def api_missing_required_courses():
            with_update = request.args.get('withUpdate', 'false').lower() == 'true'
            return jsonify(api_instance.missing_required_courses(withUpdate=with_update))

        @app.route('/api/course_selection_by_course_code', methods=['GET'])
        def api_course_selection_by_course_code():
            with_update = request.args.get('withUpdate', 'false').lower() == 'true'
            return jsonify(api_instance.course_selection_by_course_code(withUpdate=with_update))

        @app.route('/api/courses_we_have_this_semester', methods=['GET'])
        def api_courses_we_have_this_semester():
            with_update = request.args.get('withUpdate', 'false').lower() == 'true'
            return jsonify(api_instance.courses_we_have_this_semester(withUpdate=with_update))

        @app.route('/api/get_score', methods=['GET'])
        def api_get_score():
            return jsonify(api_instance.get_score())

        @app.route('/api/progress_on_graduation', methods=['GET'])
        def api_progress_on_graduation():
            return jsonify(api_instance.progress_on_graduation())

        @app.route('/api/update_all_user_data', methods=['POST'])
        def api_update_all_user_data():
            return jsonify(api_instance.update_all_user_data())

        @app.route('/api/schedule_my_class', methods=['POST'])
        def api_schedule_my_class():
            data = request.get_json(silent=True) or {}
            return jsonify(api_instance.schedule_my_class(data))

        @app.route('/api/search_courses', methods=['POST'])
        def api_search_courses():
            data = request.get_json(silent=True) or {}
            return jsonify(api_instance.search_courses(data))

        return app
    else:
        b_app = Bottle()

        @b_app.route('/')
        def b_index():
            return static_file('index.html', root=GUI_DIR)

        @b_app.route('/<path:path>')
        def b_static(path):
            return static_file(path, root=GUI_DIR)

        def b_json(data):
            bottle_response.content_type = 'application/json'
            return json.dumps(data)

        @b_app.route('/api/check_saved_session', method='GET')
        def b_check_saved_session():
            return b_json(api_instance.check_saved_session())

        @b_app.route('/api/authenticate', method='POST')
        def b_authenticate():
            data = bottle_request.json or {}
            return b_json(api_instance.authenticate(data.get('username', ''), data.get('password', '')))

        @b_app.route('/api/logout', method='POST')
        def b_logout():
            return b_json(api_instance.logout())

        @b_app.route('/api/student_info', method='GET')
        def b_student_info():
            with_update = bottle_request.query.get('withUpdate', 'false').lower() == 'true'
            return b_json(api_instance.student_info(withUpdate=with_update))

        @b_app.route('/api/study_progress_info', method='GET')
        def b_study_progress_info():
            with_update = bottle_request.query.get('withUpdate', 'false').lower() == 'true'
            return b_json(api_instance.study_progress_info(withUpdate=with_update))

        @b_app.route('/api/required_courses_and_graduation_credits', method='GET')
        def b_required_courses_and_graduation_credits():
            with_update = bottle_request.query.get('withUpdate', 'false').lower() == 'true'
            return b_json(api_instance.required_courses_and_graduation_credits(withUpdate=with_update))

        @b_app.route('/api/all_years_course_grades', method='GET')
        def b_all_years_course_grades():
            with_update = bottle_request.query.get('withUpdate', 'false').lower() == 'true'
            return b_json(api_instance.all_years_course_grades(withUpdate=with_update))

        @b_app.route('/api/missing_required_courses', method='GET')
        def b_missing_required_courses():
            with_update = bottle_request.query.get('withUpdate', 'false').lower() == 'true'
            return b_json(api_instance.missing_required_courses(withUpdate=with_update))

        @b_app.route('/api/course_selection_by_course_code', method='GET')
        def b_course_selection_by_course_code():
            with_update = bottle_request.query.get('withUpdate', 'false').lower() == 'true'
            return b_json(api_instance.course_selection_by_course_code(withUpdate=with_update))

        @b_app.route('/api/courses_we_have_this_semester', method='GET')
        def b_courses_we_have_this_semester():
            with_update = bottle_request.query.get('withUpdate', 'false').lower() == 'true'
            return b_json(api_instance.courses_we_have_this_semester(withUpdate=with_update))

        @b_app.route('/api/get_score', method='GET')
        def b_get_score():
            return b_json(api_instance.get_score())

        @b_app.route('/api/progress_on_graduation', method='GET')
        def b_progress_on_graduation():
            return b_json(api_instance.progress_on_graduation())

        @b_app.route('/api/update_all_user_data', method='POST')
        def b_update_all_user_data():
            return b_json(api_instance.update_all_user_data())

        @b_app.route('/api/schedule_my_class', method='POST')
        def b_schedule_my_class():
            data = bottle_request.json or {}
            return b_json(api_instance.schedule_my_class(data))

        @b_app.route('/api/search_courses', method='POST')
        def b_search_courses():
            data = bottle_request.json or {}
            return b_json(api_instance.search_courses(data))

        return b_app


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    app = create_app()
    if HAVE_FLASK:
        app.run(host=host, port=port, debug=False)
    else:
        app.run(host=host, port=port)
