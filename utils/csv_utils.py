import pandas as pd


def read_csv_safe(uploaded_file):

    encodings = [
        "utf-8",
        "utf-8-sig",
        "latin1",
        "cp1252"
    ]

    separators = [
        ",",
        ";",
        "\t"
    ]

    for enc in encodings:

        for sep in separators:

            try:

                uploaded_file.seek(0)

                df = pd.read_csv(
                    uploaded_file,
                    encoding=enc,
                    sep=sep,
                    engine="python",
                    on_bad_lines="skip"
                )

                # đảm bảo không phải file lỗi
                if len(df.columns) > 3:

                    return df

            except:
                continue

    return pd.DataFrame()
