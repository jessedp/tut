from tablo.entities.airing import Airing
from util import convert_datestr
from config import config


class Recording(Airing):
    def __init__(self, data):
        super(Recording, self).__init__(data)

    def print(self):
        # TODO: shorten desc
        # TODO: format statuses better
        # TODO: maybe shorten Desc
        # TODO: fix the display of "error"

        error = None
        if self.video_details['error']:
            error = self.video_details['error']['code'] \
                + ' - ' + self.video_details['error']['details']

        top_line = convert_datestr(self.airing_details['datetime']) + " - " \
            + f"{self.airing_details['show_title']}" \
            + f" - {self.get_title()}\n"
        if self.type == 'episode':
            print(
                f"{top_line}"
                f"{self.episode['description']}\n"
                f"Season: {self.get_epsiode_num()}"
                f"  Status: {self.video_details['state']}"
                f"  Watched: {self.user_info['watched']}"
                f"  Type: {self.type}"
            )
            if error:
                print(f"Error: {error}")

        elif self.type == 'movie':
            print(
                convert_datestr(self.airing_details['datetime']) + " - " +
                f"{self.airing_details['show_title']}\n"
                f"  Type: {self.type}"
            )
        else:
            self.dump_info()

        print('output file name:')
        print("\t" + self.get_out_path())
        print()

    def get_title(self, for_print=True):
        if not self.type == 'episode':
            return ""
        if for_print:
            title = self.episode['title']
            if not title or title == 'None':
                return self.get_epsiode_num()
            # yuck - "105" = season 1 + episode 5
            if title == str(self.episode['season_number']) + \
                    '{:02}'.format(self.episode['number']):
                return self.get_epsiode_num()
            return title
        return "WTF?"

    def get_epsiode_num(self):
        return "s{:02}".format(self.episode['season_number']) + \
            'e{:02}'.format(self.episode['number'])

    def get_out_path(self):
        if self.type == 'episode':
            title = self.airing_details['show_title']
            out = config.get('Output Locations', 'TV') + '/'
            out += title + '/'
            out += 'Season {:02}'.format(self.episode['season_number']) + '/'
            out += title + \
                ' - s{:02}'.format(self.episode['season_number']) + \
                'e{:02}'.format(self.episode['number'])
            return out + ".EXT"
        elif self.type == 'movie':
            out = config.get('Output Locations', 'Movies') + '/'
            out += f"{self.airing_details['show_title']}"
            out += f" - {self.movie_airing['release_year']}"
            return out+".EXT"
        else:
            return f"{self.type } is UNDEFINED"
