#!/usr/bin/env python3

from datetime import date
from dateutil.parser import parse as date_parser
import requests
import argparse
import json

RED = '\033[0;31m'
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color
TODAY = date.today()


class Video(object):
    '''Just an object to hold details about a video.
    Allows a convenient way for accessing the details and pretty print methods.
    '''
    def __init__(self, title, views, upload_date):
        '''Just a regular init.
        :param title: Video's title from YouTube
        :param views: Video's view count from YouTube
        :param upload_date: The data the video was uploaded to YouTube
        '''
        self.title = title
        self.views = views
        self.upload_date = upload_date

        self.days_up = (TODAY - self.upload_date).days
        self.years_up = int(self.days_up / 365)
        self.pretty_date = self.upload_date.strftime('%b %d, %Y')
        self.avg_views = self.views / self.days_up

    def __str__(self):
        '''The "pretty print" I was talking about.
        :returns: A colorful string with a brief summary of the video
        '''
        return '%s%s%s - %s%s views%s' % \
            (RED, self.title, NC, GREEN, '{:,}'.format(int(self.views)), NC)

    def full_info(self):
        '''Yay another pretty print.
        :returns: Much detailed information about the video, such as:
            Title, upload date, views count, time since upload,
            average views per day.
        '''
        output = ''

        # Summary
        output += '%s%s%s - ' % (RED, self.title, NC)
        output += 'Uploaded on %s%s%s - ' % (BLUE, self.pretty_date, NC)
        output += '%s%s views%s\n' % (GREEN, '{:,}'.format(self.views), NC)

        # Time past since upload
        output += '\t%s%s%d days%s since upload\n' % \
            (BLUE, '' if not self.years_up else '%d year%s and ' %
             (self.years_up, '' if self.years_up == 1 else 's'),
             self.days_up % 365, NC)

        # Average views per day
        output += '\t%s%s%s average views per day' % \
            (GREEN, '{:,}'.format(int(self.avg_views)), NC)

        return output

    def fast_forward(self, days=1):
        '''Progress the video forward in time so that it gets the average
        amount of views on each progressed day.
        :param days: Allows you to specify the amount of days to progress
        '''
        self.views += self.avg_views * days


def get_video_details(vid_id, key):
    '''Uses YouTube Data API v3 to gather information about the videos.
    :param vid_id: The video ID from YouTube, i.e the part after
        https://www.youtube.com/watch?v=
    :param key: The authentication key from Google. Can be found at:
        https://console.developers.google.com/ -> Credentials section.
    :returns: A Video object.
    '''
    url = 'https://www.googleapis.com/youtube/v3/videos'
    params = {
        'part': 'snippet,statistics',
        'id': vid_id,
        'key': key
    }

    resp = requests.get(url=url, params=params)
    json = resp.json()

    title = json['items'][0]['snippet']['title']
    views = int(json['items'][0]['statistics']['viewCount'])
    upload_date = \
        date_parser(json['items'][0]['snippet']['publishedAt']).date()

    return Video(title, views, upload_date)


def print_videos_summary(videos):
    '''Prints out a numbered list of the videos.
    :param videos: List of Video objects
    '''
    for i, vid in enumerate(videos):
        print('%d. %s' % (i + 1, vid))


def track_changes(videos, days_threshold=100):
    '''The main method. This method progresses the videos through time based
    on their average view count and reports for any changes, i.e if one video
    passed another.
    :param videos: List of Video objects
    :param days_threshold: Number of days to track for changes in the videos.
    '''
    # Print videos' full details
    list(map(lambda vid: print(vid.full_info()), videos))
    print()

    # Track for changes on videos' places
    prev_order = None
    for day in range(days_threshold):
        videos.sort(reverse=True, key=lambda v: v.views)

        if day == 0:
            print('Starting state (Day 1):')
            print_videos_summary(videos)
        else:
            for i, vid in prev_order.items():
                if vid.title != videos[i].title:
                    print('Day %d:' % (day + 1))
                    print_videos_summary(videos)
                    break
        prev_order = dict(enumerate(videos))

        for vid in videos:
            vid.fast_forward()


def main():
    desc = 'This program tracks and reports for changes in the given videos.'
    epi = 'More information at: '

    parser = argparse.ArgumentParser(
        description=desc, epilog=epi,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-j', metavar='JSON_file', type=str, required=True,
                        help='A path to a JSON file.', dest='json')
    parser.add_argument('-k', metavar='auth_key', type=str,
                        help='An authentication key from Google. '
                        '(if not specified in the JSON)', dest='key')
    parser.add_argument('-d', metavar='days', type=int,
                        help='Amount of days to scan for changes.')

    args = parser.parse_args()

    with open(args.json) as json_file:
        data = json.load(json_file)

        if 'videos' not in data:
            print('Please provide a list of videos in the JSON file!')
            return 1
        else:
            video_ids = data['videos']

        if 'key' in data:
            key = data['key']
        elif args.key is not None:
            key = args.key
        else:
            print('Please specify an Authentication Key!')
            return 2

    videos = [get_video_details(vid, key) for vid in video_ids]
    track_changes(videos)

if __name__ == '__main__':
    main()
