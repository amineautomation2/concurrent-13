import argparse
import time
from aviva.kiid import get_kiid_url
from aviva.total import aviva_total
from utils import clean_spreadsheet, get_xlsx_filepath
from aviva import aviva_runner
from worker import get_xlsx_data, merge_csv_to_xlsx


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
        clean_spreadsheet(xlsx)
        aviva_total()
        return

    if args.id and args.max and args.sheet:
        id = int(args.id)
        max_w = int(args.max)
        aviva_runner(id_w=id, max_w=max_w, sheet=args.sheet)
        return

    if args.merge and args.sheet:
        merge_csv_to_xlsx(xlsx, ["name", "isin", "url"], args.sheet)
        return

#    if args.id and args.max and args.kiids:
#        data = get_xlsx_data(xlsx, "MF")
#        data_per_worker = data[int(args.id)::int(args.max)]
#        get_kiid_url(id_w=int(args.id), data_per_worker=data_per_worker)
#        return

#    if args.merge and args.kiid:
#        merge_csv_to_xlsx(xlsx, ["name", "isin", "url"], "MF", "_KIID_URL")
#        return


if __name__ == "__main__":
    start = time.perf_counter()
    main()
    elapsed = time.perf_counter() - start
    print(f"Execution time: {elapsed:.2f} seconds.")
    # create_spreadsheet("aviva.xlsx",
    # ["Investment", "ETF", "MF"],
    # ["Name", "ISIN", "URL"],
    # )
