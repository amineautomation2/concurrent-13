from aviva.mf import isin_from_pdf

url = "https://www.fundslibrary.co.uk/FundsLibrary.DataRetrieval/Documents.aspx?type=packet_fund_unit_doc_kiid&docid=1933586a-a189-4820-a59f-58f5e33a3887&user=5gcJUmftGMKN6oUT6gRDwtadoNmTgF0vm%2bW292JUKLk%3d"
data = isin_from_pdf(url)
