from wa import inline, blocks, render_post


def test_bold_and_italic():
    assert inline("*Bold* and _italic_.") == "<strong>Bold</strong> and <em>italic</em>."


def test_html_is_escaped_before_formatting():
    assert inline("Tom & *Jerry* <3") == "Tom &amp; <strong>Jerry</strong> &lt;3"


def test_asterisk_with_space_after_is_not_bold():
    assert inline("2 * 3 = 6") == "2 * 3 = 6"


def test_url_becomes_link_and_underscores_inside_it_are_safe():
    out = inline("see https://example.org/a_b_c now")
    assert out == 'see <a href="https://example.org/a_b_c">https://example.org/a_b_c</a> now'


def test_blocks_split_on_blank_lines_and_trim():
    assert blocks("a\n\n\n b \n\nc\n") == ["a", "b", "c"]


def test_render_post_title_and_paragraphs():
    body = "*Family history — 21 September*\n\nFirst para.\nsecond line\n\nRead past updates: https://x.test/y/\n"
    title, html = render_post(body)
    assert title == "Family history — 21 September"
    assert html == (
        "<p>First para.<br>\nsecond line</p>\n"
        '<p class="link">Read past updates: <a href="https://x.test/y/">https://x.test/y/</a></p>'
    )


def test_render_post_empty():
    assert render_post("") == ("", "")
