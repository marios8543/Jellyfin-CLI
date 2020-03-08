from jellyfin_cli.jellyfin_client.data_classes.Items import Item
from datetime import datetime

class Movie(Item):
    def __init__(self, res, context):
        super().__init__(res, context)
        self.subbed = res["HasSubtitles"] if "HasSubtitles" in res else False
        if "PremiereDate" in res:
            self.premiered = datetime.strptime(res["PremiereDate"].split("T")[0], "%Y-%m-%d")
        else:
            self.premiered = None
        self.rating = res["OfficialRating"] if "OfficialRating" in res else None
        self.community_rating = res["CommunityRating"] if "CommunityRating" in res else None


