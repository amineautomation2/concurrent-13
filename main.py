import argparse
from aviva.kiid import get_kiid_url
from utils import get_xlsx_filepath
from aviva import aviva_runner, aviva_total
from worker import merge_csv_to_xlsx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=str)
    parser.add_argument("--max", type=str)
    parser.add_argument("--sheet", type=str)
    parser.add_argument("--total", action="store_true")
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--kiid", action="store_true")
    args = parser.parse_args()
    xlsx = get_xlsx_filepath("aviva.xlsx")
    if args.total:
        aviva_total()
        return

    if args.id and args.max and args.sheet:
        id = int(args.id)
        max_w = int(args.max)
        aviva_runner(id_w=id, max_w=max_w, sheet=args.sheet)
        return

    if args.id and args.max and args.kiid:
        id = int(args.id)
        max_w = int(args.max)
        get_kiid_url(id_w=id, max_w=max_w)
        return

    if args.merge and args.sheet:
        merge_csv_to_xlsx(xlsx, ["name", "isin", "url"], args.sheet)
        return

    if args.merge and args.kiid:
        merge_csv_to_xlsx(xlsx, ["name", "isin", "url"], "MF", "_KIID")
        return


if __name__ == "__main__":
    main()
    # create_spreadsheet("aviva.xlsx",
    # ["Investment", "ETF", "MF"],
    # ["Name", "ISIN", "URL"],
    # )
