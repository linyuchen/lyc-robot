__doc__ = """
A convenient module for handle html
@author: LinYuChen
@version:1.5
"""

import re


def get_form(data: str, tag="postfield", encoding="utf8") -> dict:
    """
    get the form from data

    @param data:the html text
    @type data:string

    @param tag:the post tag of form,for example：<input name = "id"...> the tag is input
    @type tag:string

    @param encoding:post data encoding
    @type:string

    @return:post data
    @rtype param:
    """
    param = {}
    field_list = re.findall(tag + ".*? name=\"(.*?)\".*?value=\"(.*?)\"", data)

    for i in field_list:
        param[i[0]] = i[1].encode(encoding)

    return param


def remove_char_entity(html: str):
    char_entity_dict = {
        "&nbsp;": " ", "&lt;": "<", "&gt;": ">", "&amp;": "&", "&quot;": "\"",
        "&apos;": "'", "&plusmn;": "+",
    }

    for i in char_entity_dict:
        # noinspection PyBroadException
        try:
            html = html.replace(i, char_entity_dict[i])
        except:
            pass

    def func(m):

        entity_ascii = int(m.group(1))
        if entity_ascii < 256:
            return chr(entity_ascii)
        else:
            return ""

    html = re.sub(r"&#(\d+);", func, html)

    return html


def change2char_entity(s: str) -> str:
    s = s.replace("&", "&amp;")
    char_entity_dict = {
        "'": "&apos;", "\"": "&quot;", u"\u0020": "&nbsp;", "<": "&lt;", ">": "&gt;",
        "+": "&plusmn;"
    }
    for i in char_entity_dict:
        s = s.replace(i, char_entity_dict[i])

    return s


def html2txt(html: str) -> str:
    """
    @param html: html text
    @type: string

    @return: The converted txt
    @rtype: string
    """

    html = re.sub("(\r\n)+", "", html)
    html = re.sub("\n+", "", html)
    html = re.sub("\t+?", "", html)
    html = re.sub(" +", " ", html)
    pattern = re.compile("<!--.*?-->", re.S)
    html = re.sub(pattern, "", html)  # remove the comment
    html = remove_char_entity(html)
    # while "</style>" in html:
    html = re.sub("<style.*?>.*?</style>", "", html)  # remove the style

    pattern = re.compile("<script[^>]*?>.*?</script>", re.S)
    # while "</script>" in html:
    html = re.sub(pattern, "", html)  # remove the script
    # replace the <br/>
    html = re.sub(u"<br[^>]*?>", "\n", html)
    html = re.sub(u"<p[^>]*?>", "\n", html)
    html = re.sub(u"<h[^>]*?>", "\n\n", html)
    html = re.sub(u"<li[^>]*?>", "\n", html)
    #        html = re.sub(u"</li>","\n",html)

    html = re.sub(u"</div>", "\t", html)
    #       表格处理
    html = re.sub(u"</th>", "\t", html)
    html = re.sub(u"<tr[^>]*?>", "\n", html)
    #        html = re.sub(u"</tr>","\n",html)
    html = re.sub(u"</td>", "\t", html)

    html = re.sub(u"<[^>]*?>", "", html)  # remove the tag
    #        html = re.sub("</[^>]*?>","",html)# remove the end tag
    #        print html
    #        pattern = re.compile("<.*?/>",re.S)
    #        html = re.sub("<[^>]*?/>","",html)# remove the startend tag


    return html


def txt2html(txt: str) -> str:
    html = change2char_entity(txt)
    html = html.replace("\n", "<br/>")

    return html


def _get_tag_attrs(tag: str, tag_html: str) -> dict:
    tag_html = re.findall("<%s[^>]*?>" % tag, tag_html)[0]
    #        print tag_html
    attrs_list = re.findall(r"\s*(\S*)\s*=\s*[\"'](.*?)[\"']\s*", tag_html)  # get attributes
    #        print attrs_list
    _attrs = {}
    for key in attrs_list:
        _attrs[key[0]] = key[1]

    return _attrs


def get_start_tag(html, tag, attrs: None | dict = None) -> list[str]:
    if attrs is None:
        attrs = {}
    result = re.findall("<%s[^>]*?>" % tag, html)
    start_tag_list = []
    for i in result:

        _attrs = _get_tag_attrs(tag, i)

        is_attrs = True
        for key in attrs:
            if key not in _attrs or not re.findall(attrs[key], _attrs[key]):
                is_attrs = False

        if not attrs:
            is_attrs = True

        if is_attrs:
            start_tag_list.append(i)

    return start_tag_list


def get_tag_html(html: str, tag: str, attrs: None | dict = None, end_tag="") -> list[str]:
    """
    @param html: html string
    @type: str

    @param tag
    @type: str

    @param attrs: {"attribute name": "attribute value"}, value support regular
    """

    if attrs is None:
        attrs = {}
    start_tag = get_start_tag(html, tag, attrs)
    result_list = []
    end_tag = "</%s>" % tag

    def get_end_tag_pos(start_pos, __end_pos):

        tag_count = html[start_pos + 1:__end_pos].count("<" + tag)
        start_pos = __end_pos
        if not tag_count:
            return __end_pos
        for i in range(tag_count):
            p = html.find(end_tag, __end_pos + 1)
            if p != -1:
                __end_pos = p
        return get_end_tag_pos(start_pos, __end_pos)

    start_tag_pos = -1
    for i in start_tag:
        start_tag_pos = html.find(i, start_tag_pos + 1)
        end_tag_pos = html.find(end_tag, start_tag_pos + 1)
        if end_tag_pos != -1:
            end_pos = get_end_tag_pos(start_tag_pos, end_tag_pos)
        else:
            # 如果找不到</tag，则找/>
            end_pos = html.find("/>", start_tag_pos + 1)
            # 如果找不到/>，则找>
            if end_pos == -1:
                end_pos = html.find(">", start_tag_pos + 1)
        result_list.append(html[start_tag_pos:end_pos + len(end_tag)])

    return result_list


def get_tag_attrs(html: str, tag: str, attrs: None | dict = None) -> list[dict]:
    """
    @param html:html
    @type html:string

    @param tag: html tag
    @type tag: string

    @param attrs:attribute dic,{"class":"c"}
    @type attrs: dict
    
    @return: attrs
    @rtype: dict
    """

    if attrs is None:
        attrs = {}
    tag_html_list = get_tag_html(html, tag, attrs)
    _attrs = []

    for i in tag_html_list:
        _attrs.append(_get_tag_attrs(tag, i))

    return _attrs


def remove_tag(html: str, tag: str, attrs=None):
    if attrs is None:
        attrs = {}
    tag_html_list = get_tag_html(html, tag, attrs)

    result_html = html
    for i in tag_html_list:
        result_html = result_html.replace(i, "")

    return result_html
