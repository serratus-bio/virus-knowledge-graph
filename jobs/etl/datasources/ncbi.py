import os
import urllib.request as urllib
import zipfile


EXTRACT_DIR = '/tmp/new_taxdump'

def download_and_extract_tax_dump():
  if os.path.isdir(EXTRACT_DIR):
     return
  url = 'https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.zip'
  zip_path, _ = urllib.request.urlretrieve(url)
  with zipfile.ZipFile(zip_path, "r") as f:
      f.extractall(EXTRACT_DIR)


def parse_tax_dump():
  taxon_nodes = {}
  merged_nodes = {}
  sci_names = {}
  alt_names = {}
  with open(f'{EXTRACT_DIR}/nodes.dmp', mode='r') as in_file:
      for line in in_file:
          tax_id, parent_tax_id, rank, *other = line.split('|')
          tax_id, parent_tax_id, rank = tax_id.strip(), parent_tax_id.strip(), rank.strip()
          taxon_nodes[tax_id] = {'tax_id': tax_id, 'parent_tax_id': parent_tax_id, 'rank': rank }

  with open(f'{EXTRACT_DIR}/host.dmp', mode='r') as in_file:
      for line in in_file:
        tax_id, potential_hosts, *other = line.split('|')
        tax_id, potential_hosts = tax_id.strip(), potential_hosts.strip()
        taxon_nodes[tax_id].update({ 'potential_hosts': potential_hosts })

  with open(f'{EXTRACT_DIR}/merged.dmp', mode='r') as in_file:
      for line in in_file:
          old_tax_id, new_tax_id, *other = line.split('|')
          old_tax_id, new_tax_id  = old_tax_id.strip(), new_tax_id.strip()
          merged_nodes[old_tax_id] = new_tax_id

  with open(f'{EXTRACT_DIR}/names.dmp', mode='r') as in_file:
      for line in in_file:
        tax_id, name_txt, unique_name, name_class, *other = line.split('|')
        tax_id, name_txt, unique_name, name_class = tax_id.strip(), \
        name_txt.strip().replace('"', ''), unique_name.strip(), name_class.strip()
        if name_class == 'scientific name':
          taxon_nodes[tax_id].update({'scientific_name' : name_txt })
          sci_names[name_txt] = tax_id
        else:
          alt_names[name_txt] = tax_id

  return {
    taxon_nodes: taxon_nodes,
    merged_nodes: merged_nodes,
    sci_names: sci_names,
    alt_names: alt_names,
  }