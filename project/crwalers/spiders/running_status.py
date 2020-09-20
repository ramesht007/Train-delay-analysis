# -*- coding: utf-8 -*-

# Crawl modules in the Pytorch docs to extract functions
#
# To understand how CrawlSpider works, See documentation in:
# https://docs.scrapy.org/en/latest/topics/spiders.html
import re
from docs.items import ApiItem
from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor
from w3lib.html import remove_tags


class TorchSpider(CrawlSpider):
    name = "running_status"  
    version = "1.0.0" 
    allowed_domains = ['https://runningstatus.in/history/11077']  

    # Base URL for crawling
    start_urls = [f'https://runningstatus.in/history/11077']

    # Regex rules for compiling a string to a Regex object.
    split_def = re.compile(r'^([\w\.]+)\(([\w,\s=\*\'\.\-]*)\)')

  
    rules = (
        Rule(LinkExtractor(
            allow=(re.compile(r'.+\.html')),  
            restrict_css='.toctree-l1'),  
            callback='parse_api',),  
    )

   def parse_api(self, response):
        self.logger.info(f'Scraping {response.url}')

        # Crawls the selector to create a list of each function doc.
        fdef = response.css('dl.function')

        defs = {}  # Caches the processed call format of all functions

        
        for selector in fdef:

            cmd_info = {}  # Caches processed format of the current function

            # Stores the function call format, The dt tag contains the
            # Function call format for the currently crawled function.
            func_header = selector.css('dt')

            # Preprocesses func_header and stores the processed representation.
            # For example, in the format - torch.this_is_a_function(obj)¶
            text = (remove_tags(func_header.get())
                    .replace('\n', '')
                    .replace('\\', '')
                    .replace('&gt', '')
                    .replace('&lt', '')
                    .replace(' ', '')
                    .replace('[source]', ''))
            if 'torchvision' in text:
                continue

            # Uses the Regex rules to compile the function call
            split_cmd = self.split_def.match(text)

            if split_cmd is None:
                continue

            # Extracts only the function name from the Regex encoded text
            function_name = split_cmd.groups()[0].split('.')[-1]

            cmd_info['code'] = text  # Caches the formatted function call

            # Extracts every function input parameter and stores in a list
            params = split_cmd.groups()[1].split(',')

            # Caches only Default parameters
            cmd_info['args'] = [p for p in params if '=' not in p]

            # Caches other parameters
            cmd_info['kwargs'] = [p.split('=') for p in params if '=' in p]

            # Stores the function cache in the global function cache
            defs[function_name] = cmd_info

        # Loops through the global function cache to yield each function.
        for function_name, cmd_info in defs.items():

            print(function_name)
            item = ApiItem()

            item['code'] = cmd_info['code']  # Caches the function call
            item['function_name'] = function_name  # Caches the function name
            item['args'] = cmd_info['args']  # Caches the default paramaters
            item['kwargs'] = cmd_info['kwargs']  # Caches other parameters

            # Yields a structured representation of the function call format.
            yield item
