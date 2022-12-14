from django.contrib import admin

from .models import Auction, Bid, Comment, Watchlist, Category,User


# We've registered modules that are readily available from django 
admin.site.register(Auction)
admin.site.register(Bid)
admin.site.register(Comment)
admin.site.register(Watchlist)
admin.site.register(Category)
admin.site.register(User)