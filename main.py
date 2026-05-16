from utils import create_spreadsheet, get_xlsx_filepath
from aviva import aviva_runner, aviva_total
import argparse

from worker import merge_csv_to_xlsx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=str)
    parser.add_argument("--max", type=str)
    parser.add_argument("--sheet", type=str)
    parser.add_argument("--total", action="store_true")
    parser.add_argument("--merge", action="store_true")
    args = parser.parse_args()
    if args.total:
        aviva_total()
        return
    if args.id and args.max and args.sheet:
        id = int(args.id)
        max_w = int(args.max)
        aviva_runner(id_w=id, max_w=max_w, sheet=args.sheet)
        return
    if args.merge and args.sheet:
        xlsx = get_xlsx_filepath("aviva.xlsx")
        merge_csv_to_xlsx(xlsx, ["name", "isin", "url"], args.sheet)
        return
    pass


if __name__ == "__main__":
    main()
    # create_spreadsheet("aviva.xlsx",
    # ["Investment", "ETF", "MF"],
    # ["Name", "ISIN", "URL"],
    # )
