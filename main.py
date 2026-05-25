import argparse
import time
from aviva.kiid import get_kiid_url
from aviva.mf import get_kiid_urls_per_worker
from aviva.total import aviva_total
from utils import clean_spreadsheet, get_xlsx_filepath
from aviva import aviva_runner
from worker import get_xlsx_data, merge_csv_to_xlsx, read_csv, write_csv_by_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=str)
    parser.add_argument("--max", type=str)
    parser.add_argument("--sheet", type=str)
    parser.add_argument("--total", action="store_true")
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--kiid", action="store_true")
    parser.add_argument("--isin", action="store_true")
    args = parser.parse_args()
    xlsx = get_xlsx_filepath("aviva.xlsx")
    # create_spreadsheet(xlsx, ["Investment", "ETF", "MF"], ["Name", "ISIN", "URL"], col_width=35)
    if args.total:
        clean_spreadsheet(xlsx)
        aviva_total()
        return
    # Traffic left: 6124.51 MB
    if args.id and args.max and args.sheet:
        id_w = int(args.id)
        max_w = int(args.max)
        if args.sheet == "MF":
            if args.kiid:
                funds = get_xlsx_data(xlsx, args.sheet)
                csv_out = f"aviva_{id_w}_{args.sheet}_URL.csv"
                funds_kiid = get_kiid_urls_per_worker(
                    id_worker=id_w, funds=funds)
                write_csv_by_id(csv_out, funds_kiid, [
                                "name", "isin", "url", "kiid"])
                return
            if args.isin:
                # load kiid_url.json
                funds_kiid = read_csv(f"csv/aviva_{id_w}_{args.sheet}_URL.csv")
                funds_with_isin = get_kiid_url(
                    id_w=id_w, data_per_worker=funds_kiid)

                csv_out = f"aviva_{id_w}_{args.sheet}_ISIN.csv"
                write_csv_by_id(csv_out, funds_with_isin, [
                                "name", "isin", "url"])
                return
        aviva_runner(id_w=id_w, max_w=max_w, sheet=args.sheet)
        return

    if args.merge and args.sheet:
        # TODO: HANDLE MERGIN MF
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
