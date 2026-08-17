import gifos

t = gifos.Terminal(width=560, height=210, xpad=10, ypad=10, font_size=15)
t.gen_prompt(row_num=1)
t.gen_typing_text(text="whoami --verbose", row_num=1, contin=True, speed=2)
t.gen_text(
    text=[
        "future biomedical engineer, larping on GitHub",
        "some computer stuff, some medical stuff",
        "",
        "\x1b[36mHonduras\x1b[0m  |  \x1b[35mhEDS\x1b[0m",
    ],
    row_num=3,
)
t.gen_gif()
