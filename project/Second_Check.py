#!/usr/bin/python
# -*- coding: utf-8 -*-

from elasticsearch import Elasticsearch
import json

def get_date_flow(es,gte,lte,time_zone,dip):
	search_option = {
		"size": 0,
		"query": {
			"bool": {
				"must": [
					{
						"query_string": {
							"query": "dip:{}".format(dip),
							'analyze_wildcard': True
						}
					},
					{
						"range": {
							"@timestamp": {
								"gte": gte,
								"lte": lte,
								"format": "yyyy-MM-dd HH:mm:ss",
								"time_zone": time_zone
							}
						}
					}
				],
				"must_not": []
			}
		},
		"_source": {
			"excludes": []
		},
		"aggs": {
			"sip": {
				"terms": {
					"field": "sip",
					"size": 100,
					"order": {
						"flow": "desc"
					}
				},
				"aggs":{
					"flow": {
						"sum": {
							"field": "flow"
						}
					},
					"date": {
						"date_histogram": {
							"field": "@timestamp",
							"interval": "1m",
							"time_zone":time_zone,
							"min_doc_count": 1
						},
						"aggs": {
							"flow": {
								"sum": {
									"field": "flow"
								}
							}
						}	
					}
				}
			}
		}
	}
	result = es.search(
		index = "tcp-*",
		body  = search_option
	)
	return result

def calc_median(datalist):
	datalist.sort()
	half = len(datalist) // 2
	return (datalist[half]+datalist[~half])/2.0

def calc_MAD(datalist):
	median = calc_median(datalist)
	return calc_median([ abs(data-median) for data in datalist ])
	
def main(es,gte,lte,time_zone,dip):
	res = get_date_flow(es=es,gte=gte,lte=lte,time_zone=time_zone,dip=dip)
	ret_siplist = []
	for sip_item in res["aggregations"]["sip"]["buckets"]:
		datelist = []
		flowlist = []
#		print sip_item
		for item in sip_item["date"]["buckets"]:
			datelist.append(item["key"])
			flowlist.append(item["flow"]["value"])
		if len(datelist)<2:
			continue
		date_dev = [datelist[i+1]-datelist[i]  for i in range(len(datelist)-1)]
#		print date_dev
#		print flowlist
#		print calc_MAD(date_dev)
#		print calc_MAD(flowlist)
		if (calc_MAD(date_dev) <= 60000) and (calc_MAD(flowlist) == 0):
			ret_siplist.append(sip_item["key"])
	return ret_siplist		

#es = Elasticsearch([{'host':'10.2.7.33','port':'9200'}])
#siplist = main(es=es,gte="2018-05-27 16:58:00",lte="2018-05-28 16:58:00",time_zone="+08:00",dip="89.185.44.100")
#print siplist





