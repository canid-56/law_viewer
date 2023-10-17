import re
import streamlit as st


# あとは第何条何項とかのやつも省略したい


class ParenthesisReplacer:

    repr_id = 0

    def __init__(self, text, target="（）", indicator="*", divider="``", ):
        self.raw_text = text
        self.pattern = f"({target[0]}[^{target[0]}{target[1]}]+?{target[1]})"
        self.indicator = indicator
        self.matchings = {}
        self.replaced = text
        if len(divider) > 1:
            self.divider = divider
        else:
            self.divider = divider * 2

    @classmethod
    def update_repr_id(cls):
        cls.repr_id += 1

    def _replace_p(self, matching):
        rep = f"{self.divider[0]}{self.indicator}{self.repr_id}{self.divider[1]}"
        # self.repr_id += 1
        self.update_repr_id()
        return rep

    def replace_n(self):
        def _replace_n(matching):
            rep = f" ({matching.group()[1:-1]}) "
            return rep
        pattern = r"(（[０-９]+?）)"
        self.replaced = re.sub(pattern, _replace_n, self.replaced)
        
    def math_once(self):
        initial_id = self.repr_id
        matchings = re.findall(self.pattern, self.replaced)
        n_matches = len(matchings)
        if n_matches > 0:
            replaced = re.sub(self.pattern, self._replace_p, self.replaced)
            self.replaced = replaced
            last_id = self.repr_id
            match_id = [f"{self.indicator}{i}" for i in range(initial_id, last_id)]
            match_dict = dict(zip(match_id, matchings))
            self.matchings.update(match_dict)

        return n_matches
    
    def replace(self):
        self.replace_n()
        while True:
            n_matches = self.math_once()
            if n_matches == 0:
                break
        
        return self.replaced


class XmlElement():

    def __init__(self):
        pass


    def __repr__(self):
        kws = [f"{k}={v}" if type(v) != list else f"len({k})={len(v)}" for k,v in self.__dict__.items()]
        return f"{type(self).__name__}({', '.join(kws)})"
    

    def __str__(self):
        if hasattr(self, "text"):
            string = self.text
        elif hasattr(self, "title"):
            string = self.title
        else:
            string = self.__repr__()
        return string
        

    # 再起的にJSON的な構造にする
    def get_structure(self):
        structure = {}
        for k,v in self.__dict__.items():
            if type(v) == list:
                st = []
                for c in v:
                    if isinstance(c, XmlElement):
                        st.append(c.get_structure())
                    else:
                        st.append(c)
                structure[k] = st
            elif isinstance(v,XmlElement):
                structure[k] = v.get_structure()
            else:
                structure[k] = v
        return structure
    
    def display(self):
        self.display_child()
    
    # 小要素のdisplayメソッドを実行する
    def display_child(self, *args, **kwargs):
        for k,v in self.__dict__.items():
            if type(v) == list:
                for c in v:
                    if isinstance(c, XmlElement):
                        c.display(*args, **kwargs)
            elif isinstance(v, XmlElement):
                v.display(*args, **kwargs)
            else:
                pass

class Sentence(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        # 文 (Sentence) は番号 (Num) を持つ
        self.num = xml.attrib["Num"]
        # 文 (Sentence) は描画モード (Mode) を持つ
        self.mode = xml.attrib["WritingMode"]
        # 文 (Sentence) はその内容 (text) を持つ
        self.text = xml.text

    def omit_parathesis(self, omit=False):
        replacer = ParenthesisReplacer(self.text)
        replaced = replacer.replace()
        replacement = replacer.matchings

        return replaced, replacement

    # 受け取った接頭辞を強調しつつ、本文を表示する
    def display(self, prefix=None, omit_state_name=None, *args, **kwargs):
        if omit_state_name is not None:
            omit_status = st.session_state[omit_state_name]
        else:
            omit_status = False

        if omit_status:
            text, replacement = self.omit_parathesis(omit_status)
        else:
            text = self.text
        # if omit_status:
        #     text = "Omit!"
        # else:
        #     text = self.text
        # st.write(st.session_state["omit"])
        if prefix:
            st.markdown(f"**{prefix}** {text}")
        else:
            st.markdown(f"{text}")
            # st.components.v1.html(f"{self.text}")

        if omit_status:
            for repr_id, repr in replacement.items():
                st.caption(repr_id + repr)



class Column(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        # 列 (Column) は 番号 (Num) を持つ
        self.num = xml.attrib["Num"]
        # 列 (Column) は 文 (Sentence) を持つ
        self.sentence = Sentence(xml.find("Sentence"))

    def display(self, *args, **kwargs):
        self.display_child(*args, **kwargs)

class ParagraphSentence(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        # 段落文 (ParagraphSentence) は 文 (Sentence) を持つ
        self.sentence = Sentence(xml.find("Sentence"))

    # 段落番号を渡す
    def display(self, disp_num=None, *args, **kwargs):
        if disp_num:
            prefix = f"{disp_num}"
        else:
            prefix = ""
        self.display_child(prefix=prefix, *args, **kwargs)

class ItemSentence(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        # 項目文 (ItemSentence) は列 (Column) を複数持つ場合があり、そうでなければ文 (Sentence) を持つ
        columns = xml.findall("Column")
        if columns:
            pass
            self.sentence = None
            self.columns = list(map(lambda xml:Column(xml),columns))
        else:
            self.sentence = Sentence(xml.find("Sentence"))
            self.columns = []

    def __getitem__(self, ind):
        return self.columns[ind]

    # 項目番号を渡す
    def display(self, title=None, *args, **kwargs):
        if title:
            prefix = f"{title}"
        else:
            prefix = ""
        self.display_child(prefix=prefix, *args, **kwargs)
        

class Item(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        # 項目 (Item) は番号 (Num) を持つ
        self.num = xml.attrib["Num"]
        # 項目 (Item) は題 (Title) を持つ
        self.title = xml.find("ItemTitle").text
        # 項目 (Item) は項目文(ItemSentence) を持つ
        self.item_sentence = ItemSentence(xml.find("ItemSentence"))

    # 項目番号を渡す
    def display(self, *args, **kwargs):
        self.display_child(title=self.title, *args, **kwargs)



class Paragraph(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        # 段落 (Paragraph) は番号 (Num) を持つ
        self.num = xml.attrib["Num"]
        # 段落 (Paragraph) は表示番号 (DisplayNum) を持つ場合がある
        disp_num = xml.find("ParagraphNum").text
        if disp_num:
            self.disp_num = disp_num
        else:
            self.disp_num = None
        # 段落 (Paragraph) は段落文 (ParaprahSentence) を持つ
        self.paragraph_sentence = ParagraphSentence(xml.find("ParagraphSentence"))
        # 段落 (Paragraph) は項目 (Item) を複数持つ場合がある
        items = xml.findall("Item")
        if items:
            self.items = list(map(lambda xml:Item(xml),items))
        else:
            self.items = []

    def __getitem__(self, ind):
        # if hasattr(self, "items"):
        return self.items[ind]
        # else:
        #     return None


    # 段落番号を渡す
    def display(self, *args, **kwargs):
        self.display_child(disp_num=self.disp_num, *args, **kwargs)


class Article(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        # 条 (Article) は番号 (Num) を持つ
        self.num = xml.attrib["Num"]
        # 条 (Article) は見出し (Caption) を持つ場合がある
        caption = xml.find("ArticleCaption")
        if caption is not None:
            self.caption = caption.text
        else:
            self.caption = None
        # 条 (Article) は題 (Title) を持つ
        self.title = xml.find("ArticleTitle").text
        # 条 (Article) は段落 (Paragraph) から成り立つ
        paragraphs = xml.findall("Paragraph")
        self.paragraphs = list(map(lambda xml:Paragraph(xml),paragraphs))

    def __getitem__(self, ind):
        return self.paragraphs[ind]

    # 見出しはレベル4、条題はレベル5の見出しで表示する
    def display(self, *args, **kwargs):
        if self.caption:
            st.divider()
            st.markdown(f"#### {self.caption}")
        st.markdown(f"##### {self.title}")
        self.display_child(*args, **kwargs)


class Chapter(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        # 章 (Chapter) は番号 (Num) を持つ
        self.num = xml.attrib["Num"]
        # 章 (Chapter) は題 (Title) を持つ
        self.title = xml.find("ChapterTitle").text
        # 章 (Chapter) は条 (Article) から成り立つ
        articles = xml.findall("Article")
        self.articles = list(map(lambda xml:Article(xml),articles))

    def __getitem__(self, ind):
        return self.articles[ind]

    # 章題を折りたたみで表示する
    def display(self, *args, **kwargs):
        # st.markdown(f"### {self.title}")
        with st.expander(f"{self.title}"):
            self.display_child(*args, **kwargs)
        

class MainProvision(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        # 本文は章 (Chapter) から成り立つ
        chapters = xml.findall("Chapter")
        self.chapters = list(map(lambda xml:Chapter(xml),chapters))
        if "omit_state_name" in kwargs:
            self.omit_state_name = kwargs["omit_state_name"]
        else:
            self.omit_state_name = None

    def __getitem__(self, ind):
        return self.chapters[ind]

    def display(self, *args, **kwargs):
        self.display_child(omit_state_name=self.omit_state_name)
        
class TocSupplProvision(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        self.label = xml.find("SupplProvisionLabel").text


class ArticleRange(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        self.text = xml.text

    def display(self, level=0, *args, **kwargs):
        st.markdown(f"{'#'*level} {self.text}")
        level += 1
        self.display_child(level=level)



class TocSection(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        self.num = xml.attrib["Num"]
        self.title = xml.find("SectionTitle").text
        self.article_range = ArticleRange(xml.find("ArticleRange"))

    def display(self, level=0, *args, **kwargs):
        st.markdown(f"{'#'*level} {self.title}")
        level += 1
        self.display_child(level=level)



class TocChapter(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        self.num = xml.attrib["Num"]
        self.title = xml.find("ChapterTitle").text
        article_range = xml.find("ArticleRange")
        if article_range is not None:
            self.article_range = ArticleRange(article_range)
        sections = xml.findall("TOCSection")
        if sections is not None:
            self.sections = list(map(lambda xml:TocSection(xml), sections))

    def display(self, *args, **kwargs):
        level =4
        st.markdown(f"{'#'*level} {self.title}")
        level += 1
        self.display_child(level=level)



class Toc(XmlElement):

    def __init__(self, xml, *args, **kwargs):
        super().__init__()
        self.label = xml.find("TOCLabel").text
        chapters = xml.findall("TOCChapter")
        if chapters is not None:
            self.chapters = list(map(lambda xml:TocChapter(xml), chapters))
        suppl = xml.find("TOCSupplProvision")
        if suppl is not None:
            self.suppl = TocSupplProvision(suppl)

    def display(self, *args, **kwargs):
        st.markdown(f"# {self.label}")
        self.display_child()

