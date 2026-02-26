from tools.downloader import Downloader


def main():

    query = input("Enter topic: ").strip()

    downloader = Downloader(output_dir="output")

    downloader.run_all(query)


if __name__ == "__main__":
    main()