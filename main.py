import requests, sys, csv
from bs4 import BeautifulSoup

def get_page(url):
    """
    Downloads the webpage from the provided URL and returns a BS object.
    """
    page = requests.get(url)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, 'html.parser')
    return soup

def check_args(args):
    """
    Check the validity of provided arguments: their number and if a correct URL has been provided.
    Upon valid check, returns URL and file name.
    """
    if len(args) != 3:
        sys.exit("Error: Incorrect number of arguments")
    url = args[1]
    file_name = args[2]
    if "volby.cz" not in url:
        sys.exit("Error: incorrect URL")
    return url, file_name

def get_munis(soup):
    """
    Searches for tables and cells containing sought after information (code of the municipality and its name).
    Returns a list of triplets: municipality code, name and complete URL address for accessing voting statistics.
    """
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

def get_muni_stats(soup):
    """
    Extracts data from a specific table containing the sought out voting statistics.
    Returns a dictionary containing the number of voters, issued envelopes and valid votes.
    """
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
    """
    Returns a dictionary containing a complete list of political parties and their respective
    vote counts.
    """
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
    """
    Compiles the previous functions to create a cohesive dataset for an individual municipality and
    returns a dictionary.
    """
    soup = get_page(url)
    town = get_muni_stats(soup)
    votes = get_party_stats(soup)
    row = {"Kód obce": code, "Název obce" : name}
    row.update(town)
    row.update(votes)
    return row

def csv_writer(file_name, rows):
    """
    Creates a CSV file with a name provided on a command line.
    Apart from the fixed columns shared between municipalities, columns are added
    dynamically based on the voted for parties.
    """
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
    """
    Main function of the program; ensures that data from all gathered municipalities
    are written into the CSV file.
    """
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