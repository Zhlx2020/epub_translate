from book_maker.loader.epub_loader import EPUBBookLoader

from my_translator import NewApiTranslator



if __name__ == "__main__":
    # 1. 配置输入epub路径
    input_epub = "testbooks/c1.epub"  # 替换为你的epub文件路径

    # 多模型池


    # 通过 prompt_config 传递 model_pool
    loader = EPUBBookLoader(
        epub_name=input_epub,
        model=NewApiTranslator,
        resume=False,
        language="zh-hans",
        key=""
    )

    loader.make_bilingual_book()
    print("翻译完成！")