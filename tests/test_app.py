from streamlit.testing.v1 import AppTest


def test_streamlit_app_renders_and_generates_action():
    app = AppTest.from_file("demo/app.py", default_timeout=20)
    app.run()

    assert not app.exception
    assert [title.value for title in app.title] == ["邻校掌柜"]
    assert [tab.label for tab in app.tabs] == [
        "经营动作",
        "素材工坊",
        "核销复盘",
        "两周验证看板",
    ]

    generate = next(button for button in app.button if button.label == "生成今日行动")
    generate.click().run()

    assert not app.exception
    metric_labels = [metric.label for metric in app.metric]
    assert "建议价" in metric_labels
    assert "安全底价" in metric_labels
    assert "增量贡献毛利" in metric_labels
