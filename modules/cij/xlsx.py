#!/usr/bin/env python
# coding=utf-8
"""
xlsx.py      - Script providing operation of xls/xlsx

Class Basic:
    Basic.import_source()    - import data of basic performance
    Basic.generate_chart()   - generate chart of basic performance
"""

import os
from collections import Counter
import numpy as np
import xlsxwriter as xw
import matplotlib.pyplot as plt


class Basic(object):
    """
    Function:
        1. Create a excel file;
        2. Parse a data file (.txt) which has title on first line;
        3. Translate data into array format;
        4. Filter array according to input list, which element is dict;
        5. Specify x axis, y axis, data and series;
        6. Generate sheet with the coordinate figure
        7. Close and save excel file.
    Input:
        name: Target to generate. If file was exists, it would be regenerate.
    """
    def __init__(self, name):
        self.source_sheet = None
        self.source_data = None
        self.sheet_dict = {}

        if os.path.isfile(name):
            os.remove(name)

        self.workbook = xw.Workbook(name)

    def import_source(self, sheet, source, delimiter=","):
        """
        Function:
            Save original data into specific sheet, and try to translate data to float type
        Input:
            sheet: Must be a non exists sheet
            source: File path of source
        """
        # check input parameters
        if ' ' in sheet:
            raise RuntimeError("Error sheet name: %s" % sheet)

        if not source.endswith("txt") and not source.endswith("csv"):
            raise RuntimeError("Error source name: %s" % source)

        self.source_sheet = sheet

        source_data = np.loadtxt(source, dtype=str, delimiter=delimiter)
        self.source_data = {"title": source_data[0].tolist(),
                            "data": source_data[1:]}

        cell_format_title = self.workbook.add_format({'bold': True,
                                                      'font_name': u'等线',
                                                      'bg_color': '#c5d9f1',
                                                      'rotation': 45})
        cell_format = self.workbook.add_format({'bold': False,
                                                'font_name': u'等线',
                                                'num_format': 0})

        worksheet = self.workbook.add_worksheet(sheet)
        worksheet.write_row('A1', self.source_data['title'], cell_format_title)

        _, col_num = self.source_data['data'].shape
        for i in range(col_num):
            try:
                data_array = self.source_data['data'][:, i].astype(float)
            except ValueError:
                data_array = self.source_data['data'][:, i]

            worksheet.write_column(1, i, data_array.tolist(), cell_format)

    def generate_chart(self, properties):
        """
        Function:
            Generate and save chart to specific sheet.
        Input:
            sheet: If already exists, new chart will be added below.
                   Otherwise, it would create a new sheet;
            x_axis: Specify x axis;
            y_axis: Specify y axis;
            series: Specify series;
            filters: dict type, use to filter useful data from original data;
            title: if None, the chart will create without title;
            x_axis_name: if None, use x_axis instead;
            y_axis_name: if None, use y_axis instead;
        """
        # check input parameters
        if not {'x_axis', 'y_axis', 'series', 'filters'}.issubset(set(properties.keys())):
            raise RuntimeError("Error properties: %s" % properties.keys())

        # generate chart
        mask = self.__filter_data(properties['filters'])
        chart = self.__generate_chart(mask, properties)
        sheet = properties['sheet']

        # Add work sheet
        if sheet in self.sheet_dict.keys():
            self.sheet_dict[sheet] += 1
            worksheet = self.workbook.get_worksheet_by_name(sheet)
        else:
            self.sheet_dict[sheet] = 1
            worksheet = self.workbook.add_worksheet(sheet)
        worksheet.insert_chart('B%d' % (5 + (self.sheet_dict[sheet] - 1) * 35), chart)

    def __filter_data(self, filters):
        title = self.source_data["title"]
        data = self.source_data["data"]
        row_num, _ = self.source_data['data'].shape
        mask = np.array([True] * row_num)
        for key in filters.keys():
            target = filters.get(key)
            index = title.index(key)
            mask = mask & (data[:, index] == str(target))
        return mask

    def __generate_chart(self, mask, properties):
        chart = self.workbook.add_chart({'type': 'line'})

        # Title of chart
        if 'title' in properties:
            chart.set_title({"name": properties['title']})

        # Add series to chart
        series_index = self.source_data['title'].index(properties['series'])
        series_array = np.unique(self.source_data['data'][:, series_index])
        for series_name in series_array:
            mask_serials = mask & (self.source_data['data'][:, series_index] == series_name)
            x_axis_index = self.source_data['title'].index(properties['x_axis'])
            y_axis_index = self.source_data['title'].index(properties['y_axis'])
            x_data = self.__generate_data(x_axis_index, mask_serials)
            y_data = self.__generate_data(y_axis_index, mask_serials)
            chart.add_series({'categories': x_data,
                              'values': y_data,
                              'marker': {'type': 'diamond'},
                              'name': '%s' % series_name})

        # Set properties of x/y axis
        if 'x_axis_name' not in properties:
            properties['x_axis_name'] = properties['x_axis']
        if 'y_axis_name' not in properties:
            properties['y_axis_name'] = properties['y_axis']

        chart.set_x_axis({'name': properties['x_axis_name'],
                          'name_font': {'size': 14, 'bold': False},
                          'num_font': {'italic': True}})
        chart.set_y_axis({'name': properties['y_axis_name'],
                          'name_font': {'size': 14, 'bold': False},
                          'num_font': {'italic': True}})
        chart.set_size({"x_scale": 2,
                        "y_scale": 2})

        return chart

    def __generate_data(self, x_axis_index, mask):
        if 0 <= x_axis_index <= 25:
            col_num = chr(65 + x_axis_index)
        else:
            col_num = chr(65 + x_axis_index / 26 - 1) + chr(65 + x_axis_index % 26)

        data_list = []
        for index, item in enumerate(mask):
            if item:
                data_list.append("%s!$%s$%s" % (self.source_sheet, col_num, index + 2))

        data = "=(%s)" % ",".join(data_list)

        return data

    def close(self):
        """Close work book"""
        self.workbook.close()


class Gc(object):
    """
    Function:
        1. Create a GC excel file;
        2. Parse a data file (.txt) which has title on first line;
        3. Translate data into array format;
        4. Filter array according to input list, which element is dict;
        5. Specify x axis, y axis, data and series;
        6. Generate sheet with the coordinate figure
        7. Close and save excel file.
    Input:
        name: Target to generate. If file was exists, it would be regenerate.
    """
    def __init__(self, name):
        self.dst = name
        self.sheetname_dict = {}
        self.pic_list = []
        if os.path.isfile(name):
            os.remove(name)
        self.workbook = xw.Workbook(name)

    def gen_config_sheet(self, sheetname, plist):
        """ generate configuration"""
        worksheet_cfg = self.workbook.add_worksheet(sheetname)
        cell_format = self.workbook.add_format({'bold': False, 'font_name': u'等线'})
        cell_format_title = self.workbook.add_format({'border': 0, 'align': 'center',
                                                      'bg_color': '#c5d9f1', 'font_size': 12,
                                                      'font_name': u'等线', 'bold': False})
        worksheet_cfg.set_column('A:E', 40, cell_format)
        worksheet_cfg.write_row('A1', plist[0], cell_format_title)
        for i in range(1, len(plist)):
            worksheet_cfg.write_row('A%d' % (i+1), plist[i], cell_format)

    def gen_data_sheet(self, datafile, para_meter, scale=1.75, steady_time=300):
        """
        datafile, sheetname, x_axis_name, y_axis_name, title,
        Function:
            Turn realtime bw data into picture, and save into specific sheet
        Input:
            sheetname: If already exists, new chart will be added continuely.
                       Otherwise, it would create new sheet;
            x_axis_name: x_axis name;
            y_axis_name: y_axis name;
            title: picure name;
            scale； size of picture.
        """
        filename = os.path.splitext(os.path.split(datafile)[1])[0][:-5]
        para_meter['filename'] = filename
        source_data = np.loadtxt(datafile, dtype=int, delimiter=',')[:, :3]
        is_bw = 'bw'in para_meter['title'].lower()
        file_data = process_rt_data(source_data, is_bw)
        pic_path = generate_rt_pic(file_data, para_meter, scale)
        pic_path_steady = generate_steady_rt_pic(file_data, para_meter, scale, steady_time)
        if para_meter['sheetname'] in self.sheetname_dict.keys():
            self.sheetname_dict[para_meter['sheetname']] = \
                self.sheetname_dict[para_meter['sheetname']] + 1
            chart_sheet = self.workbook.get_worksheet_by_name(para_meter['sheetname'])
        else:
            self.sheetname_dict[para_meter['sheetname']] = 1
            chart_sheet = self.workbook.add_worksheet(para_meter['sheetname'])
        chart_sheet.insert_image('B%d' %
                                 (5 + (self.sheetname_dict[para_meter['sheetname']] - 1) * 30),
                                 pic_path)
        chart_sheet.insert_image('Q%d' %
                                 (5 + (self.sheetname_dict[para_meter['sheetname']] - 1) * 30),
                                 pic_path_steady)
        self.__insert_value(chart_sheet, file_data,
                            5 + (self.sheetname_dict[para_meter['sheetname']] - 1) * 30,
                            steady_time)
        self.pic_list.append(pic_path)
        self.pic_list.append(pic_path_steady)

    def __insert_value(self, chart_sheet, data, start_row, steady_time):
        start_row = start_row + 23
        chart_sheet.set_column('Q:T', 20)
        cell_format_title = self.workbook.add_format({'border': 1, 'bold': 1,
                                                      'align': 'center', 'bg_color': '#c5d9f1',
                                                      'font_size': 12, 'font_name': u'等线'})
        cell_format = self.workbook.add_format({'border': 1, 'bold': 1, 'font_name': u'等线'})
        list_value = ["Serials", "max_value", "min_value", "avg_value"]
        chart_sheet.write_row('Q%d' % start_row, list_value, cell_format_title)
        for key in data.keys():
            if len(data[key]) < steady_time:
                steady_time = len(data[key])
            start_row = start_row + len(data.keys())
            steady_value = data[key][-1 * steady_time:]
            list_value = ["Steady State %d" % key]
            max_value = np.max(steady_value[:, 1])
            list_value.append(max_value)
            min_value = np.min(steady_value[:, 1])
            list_value.append(min_value)
            mean_value = np.mean(steady_value[:, 1])
            list_value.append(mean_value)
            list_value_offset = ["Offset %d" % key,
                                 "%.2f%%" % float((max_value - mean_value) / mean_value * 100),
                                 "%.2f%%" % float((mean_value - min_value) / mean_value * 100), '']
            chart_sheet.write_row('Q%d' % start_row, list_value, cell_format)
            chart_sheet.write_row('Q%d' % (start_row + 1), list_value_offset, cell_format)

    def closexls(self):
        """ close the xlsx"""
        self.workbook.close()


def generate_rt_pic(process_data, para_meter, scale):
    """ generate rater pic"""
    pic_path = para_meter['filename'] + '.png'
    plt.figure(figsize=(5.6 * scale, 3.2 * scale))
    for key in process_data.keys():
        plt.plot(process_data[key][:, 0], process_data[key][:, 1], label=str(key))
    plt.title(para_meter['title'])
    plt.xlabel(para_meter['x_axis_name'])
    plt.ylabel(para_meter['y_axis_name'])
    plt.legend(loc='upper left')
    plt.savefig(pic_path)
    return pic_path


def generate_steady_rt_pic(process_data, para_meter, scale, steady_time):
    """ generate rate steady"""
    pic_path_steady = para_meter['filename'] + '_steady.png'
    plt.figure(figsize=(4 * scale, 2.5 * scale))
    for key in process_data.keys():
        if len(process_data[key]) < steady_time:
            steady_time = len(process_data[key])
        plt.scatter(process_data[key][-1 * steady_time:, 0],
                    process_data[key][-1 * steady_time:, 1], label=str(key), s=10)
        steady_value = np.mean(process_data[key][-1 * steady_time:, 1])
        steady_value_5 = steady_value * (1 + 0.05)
        steady_value_10 = steady_value * (1 + 0.1)
        steady_value_ng_5 = steady_value * (1 - 0.05)
        steady_value_ng_10 = steady_value * (1 - 0.1)
        plt.plot(process_data[key][-1 * steady_time:, 0], [steady_value] * steady_time, 'b')
        plt.plot(process_data[key][-1 * steady_time:, 0], [steady_value_5] * steady_time, 'g')
        plt.plot(process_data[key][-1 * steady_time:, 0],
                 [steady_value_ng_5] * steady_time, 'g')
        plt.plot(process_data[key][-1 * steady_time:, 0], [steady_value_10] * steady_time, 'r')
        plt.plot(process_data[key][-1 * steady_time:, 0],
                 [steady_value_ng_10] * steady_time, 'r')
    plt.title(para_meter['title'] + '(steady)')
    plt.xlabel(para_meter['x_axis_name'] + '(steady)')
    plt.ylabel(para_meter['y_axis_name'] + '(steady)')
    plt.legend(loc='upper left')
    plt.savefig(pic_path_steady)
    return pic_path_steady


def process_rt_data(source_data, is_bw=False):
    """ process data"""
    print "source_data length:", len(source_data)
    filter_data = {}
    for index in range(2):

        filter_mask = source_data[:, 2] == index

        if np.any(filter_mask):
            filter_data[index] = sum_data(round_data(source_data[filter_mask]), is_bw)
    return filter_data


def sum_data(filter_data, is_bw):
    """ caculate sum"""
    for index in xrange(len(filter_data) - 1):
        if filter_data[index][0] > filter_data[index + 1][0]:
            max_index = index + 1
            break
    else:
        max_index = len(filter_data)
    print "max_index: ", max_index + 1
    num_jobs = int(round(len(filter_data) * 1.0 / max_index))
    print "num_jobs: ", num_jobs

    dict_time = Counter(filter_data[:, 0])
    list_sum = []
    for time_index in xrange(1, max_index + 1):

        if dict_time.get(time_index * 1000, 0) != num_jobs:
            print "[WARNING] Time %d, number of data %d != num_jobs %d" \
                  % (time_index * 1000, dict_time.get(time_index * 1000, 0), num_jobs)
            continue
        filter_mask = (filter_data[:, 0] == time_index * 1000)

        sum_rst = np.sum(filter_data[filter_mask][:, 1])
        if is_bw:
            sum_rst = sum_rst / 1024
        list_sum.append([time_index, sum_rst])
    return np.array(list_sum)


def round_data(filter_data):
    """ round the data"""
    for index in xrange(len(filter_data)):
        filter_data[index][0] = round(filter_data[index][0] / 100.0) * 100.0
    return filter_data
