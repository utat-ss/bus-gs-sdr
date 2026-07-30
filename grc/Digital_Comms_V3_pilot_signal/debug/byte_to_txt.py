from pathlib import Path

def byte_stream_to_signed_int_txt(input_file, max_bytes=1000):
    input_path = Path(input_file)
    output_path = input_path.with_suffix(".txt")

    with open(input_path, "rb") as f:
        data = f.read(max_bytes)


    with open(output_path, "w", encoding="utf-8") as f:
        for value in data:
            f.write(f"{value} ")

    print(f"Saved first {len(data)} signed byte values to: {output_path}")

filename = input("filename: ")
byte_stream_to_signed_int_txt(filename)
