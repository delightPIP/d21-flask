# data.py : CSV 파일을 읽어서 "쓰기 좋은 모양"으로 바꿔 주는 파일이에요
import csv                                    # CSV(표 모양 글자 파일)를 읽는 도구
from pathlib import Path                      # 파일 경로를 편하게 다루는 도구

CSV_PATH = Path(__file__).parent / "data" / "classes.csv"   # 이 파일 옆 data 폴더의 classes.csv 위치


def to_number(text, kind=float):              # 글자를 숫자로 바꾸는 작은 도우미
    text = (text or "").strip()               # 글자가 없으면 빈 글자로 보고, 앞뒤 공백을 지워요
    if text == "" or text.lower() == "nan":   # 비었거나 'nan'이라고 적혀 있으면
        return None                           # "값 없음"을 뜻하는 None을 돌려줘요 (0이 아니에요!)
    return kind(text)                         # 값이 있으면 숫자로 바꿔서 돌려줘요


def make_class(row):                          # CSV 한 줄(row)을 클래스 하나(딕셔너리)로 만들어요
    list_price = to_number(row["정가"])        # 정가: 빈칸이면 None
    discount = to_number(row["할인가"])        # 할인가: 빈칸이면 None
    sale = discount if discount is not None else list_price   # 판매가: 할인가가 있으면 할인가, 없으면 정가
    rating = to_number(row["평점"])            # 평점: 빈칸이면 None
    reviews = to_number(row["리뷰수"], int) or 0   # 리뷰 수: 비어 있으면 0

    if sale is None:                          # 판매가가 아예 없으면
        price_text = "가격 문의"               # 화면에는 '가격 문의'라고 보여줘요
    else:                                     # 판매가가 있으면
        price_text = f"{int(sale):,}원"        # 1000 단위 쉼표를 넣어서 '31,200원' 모양으로 만들어요

    if discount is not None and list_price is not None:   # 할인 중이면 (정가·할인가 둘 다 있을 때)
        old_price_text = f"{int(list_price):,}원"          # 취소선으로 보여줄 정가 글자를 만들어요
    else:                                     # 할인 중이 아니면
        old_price_text = None                 # 취소선 정가는 필요 없어요

    if rating is None:                        # 평점이 비었으면
        rating_text = "아직 리뷰가 없어요"      # 안내 문구를 보여줘요
    else:                                     # 평점이 있으면
        rating_text = f"★ {rating:.1f} ({reviews:,})"   # '★ 4.4 (213)' 모양으로 만들어요

    return {                                  # 화면과 API에서 쓸 값들을 한 묶음으로 돌려줘요
        "id": int(row["id"]),
        "category": row["카테고리"],
        "region": row["지역"],
        "name": row["클래스명"],
        "list_price": list_price,
        "discount_price": discount,
        "sale_price": sale,
        "rating": rating,
        "review_count": reviews,
        "is_new": row["NEW"].strip().lower() == "true",
        "price_text": price_text,             # 화면용 글자
        "old_price_text": old_price_text,
        "rating_text": rating_text,
    }


def load_classes():                           # 전체 클래스 목록을 읽어 오는 함수
    with open(CSV_PATH, encoding="utf-8-sig") as f:   # utf-8-sig: 엑셀이 붙인 맨 앞 숨은 글자(BOM)도 처리해요
        return [make_class(row) for row in csv.DictReader(f)]   # 한 줄씩 클래스로 바꿔 목록으로 만들어요


def get_class(class_id):                      # 번호로 클래스 하나를 찾는 함수
    for item in load_classes():               # 하나씩 살펴보다가
        if item["id"] == class_id:            # 번호가 같으면
            return item                       # 그걸 돌려줘요
    return None                               # 끝까지 없으면 None


def get_categories(classes):                  # 카테고리 이름 목록 (중복 없이, 가나다순)
    return sorted({c["category"] for c in classes})


def filter_sort(classes, category=None, sort=None):   # 거르기 + 정렬을 한 번에 해 주는 함수
    if category:                              # 카테고리가 주어졌으면
        classes = [c for c in classes if c["category"] == category]   # 그 카테고리만 남겨요
    if sort == "price":                       # 싼 순 정렬
        # (가격 없음 여부, 가격): 가격 있는 것(False)이 먼저, 가격 문의(True)는 맨 뒤
        classes = sorted(classes, key=lambda c: (c["sale_price"] is None, c["sale_price"] or 0))
    elif sort == "rating":                    # 평점 높은 순 정렬
        # 평점 없는 것은 맨 뒤로, 있는 것은 높은 평점부터
        classes = sorted(classes, key=lambda c: (c["rating"] is None, -(c["rating"] or 0)))
    return classes


def make_stats(classes):                      # 통계를 계산하는 함수
    prices = [c["sale_price"] for c in classes if c["sale_price"] is not None]   # 빈칸 뺀 판매가들
    ratings = [c["rating"] for c in classes if c["rating"] is not None]          # 빈칸 뺀 평점들
    by_category = {}                          # 카테고리별 개수를 담을 빈 상자
    for c in classes:                         # 하나씩 보면서
        by_category[c["category"]] = by_category.get(c["category"], 0) + 1   # 개수를 1씩 올려요
    return {
        "total": len(classes),                                                # 전체 개수
        "avg_sale_price": round(sum(prices) / len(prices)) if prices else None,   # 평균 판매가
        "price_inquiry_count": len(classes) - len(prices),                    # 가격 문의 수
        "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else None, # 평균 평점
        "no_review_count": len(classes) - len(ratings),                       # 리뷰 없음 수
        "by_category": by_category,                                           # 카테고리별 개수
    }
