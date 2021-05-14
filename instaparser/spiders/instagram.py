import scrapy
from scrapy.http import HtmlResponse
import re
import json
from urllib.parse import urlencode
from copy import deepcopy
from Data_collecting_hw.instaparser.items import InstaparserItem


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['http://www.instagram.com/']
    inst_login_url = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = 'login'
    inst_pass = 'password'
    parse_users = ['craftbeer78', 'ods_ai']
    followers_hash = '5aefa9893005572d237da5068082d8d5'
    following_hash = '3dec7e2c57367ef3da3d987d89f9dbc8'
    graphql_url = 'https://www.instagram.com/graphql/query/?'

    def parse(self, response:HtmlResponse):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_url,
            method='POST',
            callback=self.login,
            formdata={'username': self.inst_login, 'enc_password': self.inst_pass},
            headers={'X-CSRFToken': csrf}
        )

    def login(self, response:HtmlResponse):
        j_body = response.json()
        if j_body.get('authenticated'):
            for user in self.parse_users:
                yield response.follow(
                    f'/{user}',
                    callback=self.user_data_parse,
                    cb_kwargs={'username': user}
                )

    def user_data_parse(self, response:HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        variables = {'id': user_id, 'include_reel': True, 'fetch_mutual': False, 'first': 24}
        url_followers = f'{self.graphql_url}query_hash={self.followers_hash}&{urlencode(variables)}'
        url_following = f'{self.graphql_url}query_hash={self.following_hash}&{urlencode(variables)}'
        yield response.follow(
            url_followers,
            callback=self.user_followers_parse,
            cb_kwargs={'username': username, 'user_id': user_id, 'variables': deepcopy(variables)})
        yield response.follow(
            url_following,
            callback=self.user_following_parse,
            cb_kwargs={'username': username, 'user_id': user_id, 'variables': deepcopy(variables)})

    def user_followers_parse(self, response:HtmlResponse, username, user_id, variables):
        j_data = response.json()
        page_info = j_data.get('data').get('user').get('edge_followed_by').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info.get('end_cursor')
            url_followers = f'{self.graphql_url}query_hash={self.followers_hash}&{urlencode(variables)}'
            yield response.follow(
                url_followers,
                callback=self.user_followers_parse,
                cb_kwargs={'username': username, 'user_id': user_id, 'variables': deepcopy(variables)})
        followers = j_data.get('data').get('user').get('edge_followed_by').get('edges')
        for follower in followers:
            item = InstaparserItem(
                user_id=user_id,
                follow_id = follower.get('node').get('id'),
                follow_tag=1, # Признак follower
                follow_name = follower.get('node').get('username'),
                follow_full_name=follower.get('node').get('full_name'),
                follow_avatar=follower.get('node').get('profile_pic_url')
            )
            yield item

    def user_following_parse(self, response:HtmlResponse, username, user_id, variables):
        j_data = response.json()
        page_info = j_data.get('data').get('user').get('edge_follow').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info.get('end_cursor')
            url_following = f'{self.graphql_url}query_hash={self.following_hash}&{urlencode(variables)}'
            yield response.follow(
                url_following,
                callback=self.user_following_parse,
                cb_kwargs={'username': username, 'user_id': user_id, 'variables': deepcopy(variables)})
        following = j_data.get('data').get('user').get('edge_follow').get('edges')
        for follow in following:
            item = InstaparserItem(
                user_id=user_id,
                follow_id = follow.get('node').get('id'),
                follow_tag=0, # Признак following
                follow_name = follow.get('node').get('username'),
                follow_full_name=follow.get('node').get('full_name'),
                follow_avatar=follow.get('node').get('profile_pic_url')
            )
            yield item

    # Получение csrf токена для авторизации
    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')


    #Получаем id пользователя
    def fetch_user_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        print()
        return json.loads(matched).get('id')
