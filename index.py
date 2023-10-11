import streamlit as st
import requests
from lxml import etree

from util import MainProvision, Toc, ParenthesisReplacer

ParenthesisReplacer.repr_id = 0

API_VERSION = 1


@st.cache_resource
def get_laws(keyword=None, category=1, version=API_VERSION):
    url = f"https://elaws.e-gov.go.jp/api/{version}/lawlists/{category}"
    res = requests.get(url)
    tree = etree.fromstring(res.content)
    root = tree.getroottree()
    if keyword:
        hit = root.xpath(f"//LawNameListInfo[LawName[contains(text(),'{keyword}')]]")
    else:
        hit = root.xpath(f"//LawNameListInfo]")
    dictionalize = lambda law:dict(map(lambda elem:(elem.tag, elem.text), law))
    hit = list(map(dictionalize, hit))
    return hit

def format_law(law):
    law_name = law["LawName"]
    law_no = law["LawNo"]
    prom_date = law["PromulgationDate"]
    return f"{law_name} | {law_no} ({prom_date} 交付)"

st.title("法令読む読む君（仮）")

if "search_done" not in st.session_state:
    st.session_state["search_done"] = False

if "select_done" not in st.session_state:
    st.session_state["select_done"] = False


if "omit" not in st.session_state:
    st.session_state["omit"] = False

# 法令一覧取得

with st.expander("検索", expanded=True):

    keyword = st.text_input(label="キーワード", value="特許")
    target_law = None


    if st.button("検索をする"):
        st.session_state["search_done"] = True

    if st.session_state["search_done"]:
        laws = get_laws(keyword)
        target_law = st.selectbox(
            "一致した法令",
            laws,
            format_func=format_law
        )

        if st.button("法令を読む"):
            st.session_state["select_done"] = True

# # 法令取得

@st.cache_resource
def get_law_elems(id=None, number=None, version=API_VERSION):
    id_or_number = id if id else number
    if id_or_number:
        url = f"https://elaws.e-gov.go.jp/api/{version}/lawdata/{id_or_number}"
    else:
        raise ValueError("require id or number")
    res = requests.get(url)
    tree = etree.fromstring(res.content)
    root = tree.getroottree()
    body = root.xpath("//LawBody")[0]
    elems = body.getchildren()
    return elems


def toggle_omit():
    st.session_state["omit"] = not st.session_state["omit"]

if st.session_state["select_done"]:
    id_or_number = target_law["LawId"]
    law_elems = get_law_elems(id_or_number)
    st.header(law_elems[0].text)

    for item in law_elems[1:]:

        if item.tag == "TOC":
            with st.sidebar:
                st.toggle("省略", on_change=toggle_omit)
                toc = Toc(item)
                toc.display()
        elif item.tag == "MainProvision":
            main_provision = MainProvision(item, omit_state_name="omit")
            main_provision.display()
        else:
            # children = item.getchildren()
            # with st.expander(children[0].text):
            #     st.write(children[1:])
            pass