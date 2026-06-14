import requests, sys, csv
from bs4 import BeautifulSoup

def get_page(url):
    page = requests.get(url)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, 'html.parser')
    return soup

def check_args(args):
    if len(args) != 3:
        sys.exit("Error: Incorrect number of arguments")
    url = args[1]
    file_name = args[2]
    if "volby.cz" not in url:
        sys.exit("Error: incorrect URL")
    return url, file_name

def get_munis(soup):
    munis = []
    rows = soup.find_all('tr')
    base_url = "https://volby.cz/pls/ps2017nss/"
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        link_tag = cells[0].find("a")
        if not link_tag:
            continue
        code = cells[0].get_text(strip=True)
        name = cells[1].get_text(strip=True)
        link = link_tag.get("href", "")
        if link:
            munis.append((code, name, base_url + link))
    return munis

def get_town_stats(soup):
    stats = {"Počet voličů" : "",
             "Vydané obálky" : "",
             "Platné hlasy" : ""}
    table = soup.find("table", {"id" : "ps311_t1"})
    if not table:
        return stats
    cells = table.find_all("td")
    ids = {3 : "Počet voličů", 4 : "Vydané obálky", 7 : "Počet platných hlasů"}
    for index, name in ids.items():
        if index < len(cells):
            stats[name] = cells[index].get_text(strip=True).replace("\xa0", "")
    return stats

def get_party_stats(soup):
    all_votes = {}
    for table in soup.find_all("table", {"class" : "table"}):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            name = cells[1].get_text(strip=True)
            votes = cells[2].get_text(strip=True).replace("\xa0", "")
            if name and votes.isdigit():
                all_votes[name] = votes
    return all_votes

def data_compiler(code, name, url):
    soup = get_page(url)
    town = get_town_stats(soup)
    votes = get_party_stats(soup)
    row = {"Kód obce": code, "Název obce" : name}
    row.update(town)
    row.update(votes)
    return row

def csv_writer(file_name, rows):
    if not rows:
        return
    columns = ["Kód obce", "Název obce", "Počet voličů", "Vydané obálky", "Počet platných hlasů"]
    party_columns = []
    for key in rows[0]:
        if key not in columns:
            party_columns.append(key)
    fields = columns + party_columns
    with open(file_name, mode = "w", newline = "", encoding = "utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def main():
    url, file_name = check_args(sys.argv)
    page = get_page(url)
    munis = get_munis(page)
    rows = []
    for code, name, muni_url in munis:
        print(f"Compiling {name}, {code}")
        row = data_compiler(code, name, muni_url)
        if row:
            rows.append(row)
    csv_writer(file_name, rows)
    print("Process finished.")

if __name__ == "__main__":
    main()