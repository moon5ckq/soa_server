from flask import Flask, render_template
import urllib2
import json

app = Flask(__name__)
app.debug = True

g_result = {}

@app.route("/")
def hello():
	return "hello world"

URL_SEARCH_EXPERT = "http://arnetminer.org/services/search-expert?u=vivo&start=0&num=2000&q=%s"
URL_SEARCH_PUBLICATION = "http://arnetminer.org/services/search-publication?u=vivo&start=0&num=2000&q=%s"
URL_SEARCH_CONFERENCE = "http://arnetminer.org/services/search-conference?u=vivo&start=0&num=100&q=%s"
URL_SEARCH_PUBLICATION_BY_AUTHOR = "http://arnetminer.org/services/publication/byperson/%s"

def my_comp(u, v):
	u1 = 0
	if g_result[u].has_key("Citedby"):
		u1 += g_result[u]["Citedby"] * 0.023
	if g_result[u].has_key("rank"):
		u1 += 10.0 / (g_result[u]["rank"] + 1)
	if g_result[u].has_key("Edge"):
		u1 += g_result[u]["Edge"] * 0.01
	
	v1 = 0
	if g_result[v].has_key("Citedby"):
		v1 += g_result[v]["Citedby"] * 0.023
	if g_result[v].has_key("rank"):
		v1 += 10.0 / (g_result[v]["rank"] + 1)
	if g_result[v].has_key("Edge"):
		v1 += g_result[v]["Edge"] * 0.01
	
	ret = 0
	if u1 == v1:
		ret = 0
	elif u1 > v1:
		ret = -1
	else:
		ret = 1
	return ret


@app.route("/search/<query>")
def search(query):
	response = urllib2.urlopen((URL_SEARCH_EXPERT % query).replace(" ","%20")).read()
	data_exp = json.loads(response)["Results"]
	response = urllib2.urlopen((URL_SEARCH_PUBLICATION % query).replace(" ","%20")).read()
	data_pub = json.loads(response)["Results"]
	result = {}
	for i in xrange(0, len(data_exp)):
		result[data_exp[i]["Id"]] = {"rank" : i}
	for pub in data_pub:
		if pub.has_key("AuthorIds"):
			for author in pub["AuthorIds"]:
				if not result.has_key(author):
					result[author] = {}
				if not result[author].has_key("Citedby"):
					result[author]["Citedby"] = 0
				if not result[author].has_key("Edge"):
					result[author]["Edge"] = 0
				result[author]["Citedby"] += pub["Citedby"]
				result[author]["Edge"] += len(pub["AuthorIds"]) - 1
	global g_result
	g_result = result
	result = g_result.keys()
	result = sorted(result, my_comp)
	result.remove(-1)

	return json.dumps(result)

def rerank(result):
	better_result = result
	# do whatever you want
	return better_result

@app.route("/network/<query>")
def network(query):
	from collections import defaultdict
	response = urllib2.urlopen((URL_SEARCH_PUBLICATION % query).replace(" ","%20")).read()
	data = json.loads(response)
	# constructing coauthor network
	author_name = {}
	paper_count = defaultdict(int)
	edges = defaultdict(int)
	for item in data["Results"]:
		authors = item["Authors"].split(",")
		author_ids = item["AuthorIds"]
		for i in range(len(author_ids)):
			author_name[author_ids[i]] = authors[i]
			paper_count[author_ids[i]] += 1
			for j in range(i+1, len(author_ids)):
				key = (author_ids[i],author_ids[j])
				if key[0] > key[1]:
					key = (key[1], key[0])
				edges["%s-%s" % key] += 1
	index = 0
	author_index = {}
	result = {"nodes":[], "links":[]}
	for n in author_name:
		result["nodes"].append({"id":n, "name":author_name[n], "count":paper_count[n]})
		author_index[n] = index
		index += 1
	for e in edges:
		x = e.split("-")
		result["links"].append({"source":author_index[int(x[0])], "target":author_index[int(x[1])], "value":edges[e]})
	return json.dumps(result)

@app.route("/coauthor/")
def coauthor():
	return render_template("network.htm")


if __name__ == "__main__":
	app.run(host = "0.0.0.0", port = 5923)
