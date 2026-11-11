# app.py : 클래스로 마켓 웹 서비스 (Flask)
import os                                     # 환경 변수(컴퓨터에 적어 둔 설정)를 읽는 도구
import secrets                                # 아무도 못 맞히는 무작위 글자를 만드는 도구
from dotenv import load_dotenv                # .env 파일을 읽어 환경 변수로 올려 주는 도구 (python-dotenv)
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session   # Flask 도구들 가져오기
import data                                   # 우리가 만든 data.py (CSV 읽기 담당)
import db                                     # 우리가 만든 db.py (후기를 SQLite 에 저장 · 꺼내기 담당)

load_dotenv()                                 # 이 폴더의 .env 를 읽어요 (Render 에는 .env 가 없고 환경 변수를 직접 넣어요)

app = Flask(__name__)                         # 웹 서비스(앱) 하나 만들기
app.json.ensure_ascii = False                 # JSON에서 한글이 \uXXXX 로 깨지지 않게 해요

# 비밀 키는 코드에 적지 않고 .env(내 컴퓨터)나 환경 변수(Render)에서 읽어요
# 비어 있으면 켤 때마다 새로 만들어요 — 그러면 서버를 다시 켤 때 찜이 사라지니 꼭 넣어 주세요
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)   # flash 안내와 세션(찜)을 잠그는 열쇠

db.init_db()                                  # 앱이 시작될 때 후기 표를 만들어요 (이미 있으면 그대로 둬요)


def wish_ids():                               # 이 브라우저가 찜한 클래스 번호 목록을 꺼내는 도우미
    return session.get("wish", [])            # 세션에 "wish" 가 없으면(처음 온 브라우저) 빈 목록


@app.context_processor                        # 모든 화면(템플릿)에 공통으로 넘길 값을 정하는 곳
def common_values():
    return {"wish_count": len(wish_ids())}    # 메뉴의 '찜 목록 (개수)' 에 쓸 숫자


@app.route("/")                               # 주소 / (홈)
def home():                                   # 홈 담당 함수
    classes = data.load_classes()             # 전체 클래스를 읽어요
    return render_template("home.html",       # home.html 템플릿에
                           total=len(classes),                       # 전체 개수와
                           categories=data.get_categories(classes))  # 카테고리 목록을 넘겨요


@app.route("/about")                          # 주소 /about (소개)
def about():
    return render_template("about.html")      # about.html 화면을 보여줘요


@app.route("/hello/<name>")                   # 주소 /hello/이름 : <name> 자리에 온 글자를 변수로 받아요
def hello(name):                              # 받은 이름이 name 으로 들어와요
    return render_template("hello.html", name=name)   # 템플릿에 이름을 넘겨요


@app.route("/classes")                        # 주소 /classes (목록)
def class_list():
    category = request.args.get("category", "")   # 주소 뒤 ?category=공예 값 (없으면 빈 글자)
    sort = request.args.get("sort", "")           # 주소 뒤 ?sort=price 값
    all_classes = data.load_classes()             # 전체 목록
    shown = data.filter_sort(all_classes, category, sort)   # 거르고 정렬한 결과
    return render_template("classes.html", classes=shown,
                           categories=data.get_categories(all_classes),
                           category=category, sort=sort)     # 고른 값도 넘겨서 선택 상태를 유지해요


@app.route("/class/<int:class_id>", methods=["GET", "POST"])   # 보기(GET)와 후기 남기기(POST)를 한 주소에서
def class_detail(class_id):
    item = data.get_class(class_id)           # 번호로 찾기
    if item is None:                          # 없는 번호면
        return render_template("404.html"), 404   # 404 화면 + 진짜 상태 코드 404

    if request.method == "POST":              # 저장 버튼을 눌러서 온 요청이면
        db.add_review(                        # 후기 하나를 DB(reviews.db)에 넣어요 — 서버를 꺼도 남아요
            class_id,                                      # 어느 클래스의 후기인지
            request.form.get("nickname", ""),              # 폼의 name="nickname" 칸에 쓴 값
            request.form.get("rating", ""),                # 폼의 name="rating" 칸에서 고른 값
            request.form.get("content", ""),               # 폼의 name="content" 칸에 쓴 값
        )
        flash("후기가 저장됐어요")             # 다음 화면에서 딱 한 번만 보일 안내를 맡겨 둬요
        return redirect(url_for("class_detail", class_id=class_id))   # PRG: 저장했으면 같은 상세 화면을 GET으로 다시 열게 해요

    reviews = db.get_reviews(class_id)        # 이 클래스의 후기를 DB 에서 최신순으로 꺼내요
    wished = class_id in wish_ids()           # 이 클래스를 이미 찜했는지 (True / False)
    return render_template("detail.html", c=item, reviews=reviews, wished=wished)   # 후기 목록과 찜 여부를 넘겨요


@app.route("/class/<int:class_id>/wish", methods=["POST"])   # 찜하기 / 찜 취소 — 값을 바꾸는 일이라 POST 만 받아요
def toggle_wish(class_id):
    item = data.get_class(class_id)           # 번호로 찾기
    if item is None:                          # 없는 클래스는 찜할 수 없어요
        return render_template("404.html"), 404
    ids = list(wish_ids())                    # 지금 찜 목록을 복사해 와요
    if class_id in ids:                       # 이미 찜한 클래스면
        ids.remove(class_id)                  # 목록에서 빼고
        flash(f"'{item['name']}' 찜을 취소했어요")
    else:                                     # 아직 찜하지 않았으면
        ids.append(class_id)                  # 목록에 넣어요
        flash(f"'{item['name']}' 을(를) 찜했어요")
    session["wish"] = ids                     # 바뀐 목록을 세션에 다시 저장해요
    if request.form.get("back") == "wishlist":    # 찜 목록 화면에서 누른 거면
        return redirect(url_for("wishlist"))      # 찜 목록으로 돌아가고
    return redirect(url_for("class_detail", class_id=class_id))   # 아니면 상세 화면으로 (PRG)


@app.route("/wishlist")                       # 주소 /wishlist (내 찜 목록)
def wishlist():
    classes = [data.get_class(i) for i in wish_ids()]     # 찜한 번호마다 클래스를 찾아요
    classes = [c for c in classes if c is not None]       # 혹시 없어진 번호는 빼요
    return render_template("wishlist.html", classes=classes)


@app.route("/api/classes")                    # JSON: 전체 목록
def api_classes():
    category = request.args.get("category", "")   # ?category= 로 거르기
    items = data.filter_sort(data.load_classes(), category)   # 거른 결과
    return jsonify(count=len(items), classes=[api_item(c) for c in items])   # 개수와 목록


@app.route("/api/classes/<int:class_id>")     # JSON: 하나
def api_class(class_id):
    item = data.get_class(class_id)
    if item is None:                          # 없는 번호면
        return jsonify(error="해당 번호의 클래스가 없어요", id=class_id), 404   # JSON 에러 + 404
    return jsonify(api_item(item))


@app.route("/api/stats")                      # JSON: 통계
def api_stats():
    return jsonify(data.make_stats(data.load_classes()))


def api_item(c):                              # API에는 화면용 글자(price_text 등)를 빼고 순수 값만 보내요
    keys = ["id", "category", "region", "name", "list_price", "discount_price",
            "sale_price", "rating", "review_count", "is_new"]
    return {k: c[k] for k in keys}            # 빈칸은 None → JSON에서 null 이 돼요


@app.errorhandler(404)                        # 어떤 주소든 없는 페이지로 가면
def not_found(error):
    if request.path.startswith("/api/"):      # API 주소면 JSON 으로 알려주고
        return jsonify(error="없는 주소예요"), 404
    return render_template("404.html"), 404   # 그 외엔 404 화면 + 상태 코드 404


@app.errorhandler(500)                        # 코드가 실수해서 에러가 났을 때 (debug 가 꺼져 있을 때만 보여요)
def server_error(error):
    if request.path.startswith("/api/"):      # API 주소면 JSON 으로 알려주고
        return jsonify(error="서버에서 문제가 생겼어요"), 500
    return render_template("500.html"), 500   # 그 외엔 친절한 화면 + 상태 코드 500


if __name__ == "__main__":                    # python app.py 로 켤 때만 실행돼요
    app.run(debug=True)                       # 개발용 서버 켜기 (코드를 고치면 자동 재시작)
