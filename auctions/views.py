from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Auction, Bid, Category, Comment, Watchlist
from .forms import NewCommentForm, NewListingForm, NewBidForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist


def index(request):
    return render(request, "auctions/index.html", {
        "auctions": Auction.objects.filter(closed=False).order_by('-creation_date')
    })


def login_view(request):
    if request.method == "POST":
        # Attempting to sign the user onto the site
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # A check is performed on whether the authentication was successful or not
        if user is not None:
            login(request, user)
            # A message stating a successful login is returned
            messages.success(request, f'Welcome to Ebid Ebuy, {username}. Login was successful.')

            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "An invalid username and/or password was entered."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # A check is performed on whether the password matches during confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # When a Guest User attempts to become a Ordinary User
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def categories(request):
    return render(request, "auctions/categories.html", {
        "categories": Category.objects.all()
    })


def category(request, category_id):
    try:
        # Using a try-except block to get a list of all the current active listings of a category
        auctions = Auction.objects.filter(category=category_id, closed=False).order_by('-creation_date')
         
    except Auction.DoesNotExist:
        return render(request, "auctions/error.html", {
            "code": 404,
            "message": f"The category does not exist."
        })
   
    try:
        # Using the get method to get the category id(datbase)
        category = Category.objects.get(pk=category_id)

    except Category.DoesNotExist:
        return render(request, "auctions/error.html", {
            "code": 404,
            "message": f"The category does not exist."
        })

    return render(request, "auctions/category.html", {
        "auctions": auctions,
        "category": category
    })


@login_required(login_url="login") 
def watchlist(request):
    # A check is performed on whether the user has items in their watchlist
    try:
        #try-except block to handle when watchlist is empty
        watchlist = Watchlist.objects.get(user=request.user)
        auctions = watchlist.auctions.all().order_by('-id')
        # initializing the number of items in a watchlist to the local variable watchlistNum
        watchlistNum = watchlist.auctions.all().count()

    except ObjectDoesNotExist:
        # if a watchlist does not have any items
        watchlist = None
        auctions = None
        watchlistNum = 0
    

    return render(request, "auctions/watchlist.html", {
        # returning the listings that are populated in a watchlist
        "watchlist": watchlist,
        "auctions": auctions,
        "watchlistNum": watchlistNum
    })


@login_required(login_url="login")
def create(request):
    # checking whether the request method is POST
    if request.method == "POST":
        # creating a form instance with POST data
        form = NewListingForm(request.POST, request.FILES)

        # checking whether the form is valid or not
        if form.is_valid():
            # saving the form from data to modeling
            new_listing = form.save(commit=False)
            # saving the request of user as a seller
            new_listing.seller = request.user
            # saving the starting bid as the current/initial price
            new_listing.current_bid = form.cleaned_data['starting_bid']
            new_listing.save()

            # returning a message stating it was successfully listed
            messages.success(request, 'The item was successfully listed.')

            # redirecting the user to the index page
            return HttpResponseRedirect(reverse("index"))

        else:
            form = NewListingForm()

            # if the form is invalid, the page will be re-rendered with existing information
            messages.error(request, 'The form is invalid. Please resumbit.')
            return render(request, "auctions/create.html", {
                "form": form
            })
    
    # if the request method is GET
    else:
        form = NewListingForm()
        return render(request, "auctions/create.html", {
            "form": form
        })


def listing(request, auction_id):  
    try:
        # getting the auction listing by id from the database
        auction = Auction.objects.get(pk=auction_id)
        
    except Auction.DoesNotExist:
        return render(request, "auctions/error.html", {
            "code": 404,
            "message": "The auction does not exist or was removed."
        })

    # by default the watching flag will be set to False
    watching = False
    # by default the highest bidder when  an item is initally listed is no one (base case)    
    highest_bidder = None

    # checking wheter a listing is in the OU's watchlist
    if request.user.is_authenticated and Watchlist.objects.filter(user=request.user, auctions=auction):
        watching = True
    
    # getting the page request user
    user = request.user

    # getting the total number of bids
    bid_Num = Bid.objects.filter(auction=auction_id).count()

    # getting all the comments and ratings of the listing
    comments = Comment.objects.filter(auction=auction_id).order_by("-cm_date")

    # getting the highest bids of the listing
    highest_bid = Bid.objects.filter(auction=auction_id).order_by("-bid_price").first()
    
    # checking if the request method is GET
    if request.method == "GET":
        form = NewBidForm()
        commentForm = NewCommentForm()

        # checking if the listing is not closed
        if not auction.closed:
            return render(request, "auctions/listing.html", {
            "auction": auction,
            "form": form,
            "user": user,
            "bid_Num": bid_Num,
            "commentForm": commentForm,
            "comments": comments,
            "watching": watching
            }) 

        # once the auction is closed, should have a transfer of funds using stripe(deposot/withdrawal)
        else:
            # checking  if there is a bid currently for a listing
            if highest_bid is None:
                messages.info(request, 'The bid is closed and no bidder allowed.')

                return render(request, "auctions/listing.html", {
                    "auction": auction,
                    "form": form,
                    "user": user,
                    "bid_Num": bid_Num,
                    "highest_bidder": highest_bidder,
                    "commentForm": commentForm,
                    "comments": comments,
                    "watching": watching
                })

            else:
                # assiging the highest_bidder, using .bider to avoid confusion with .bidder
                highest_bidder = highest_bid.bider

                # checking whether the current ordinary user is the bid winner    
                if user == highest_bidder:
                    messages.info(request, 'Congratulations. You have won the bid on this item.')
                else:
                    messages.info(request, f'The winner of this bid is {highest_bidder.username}')

                return render(request, "auctions/listing.html", {
                "auction": auction,
                "form": form,
                "user": user,
                "highest_bidder": highest_bidder,
                "bid_Num": bid_Num,
                "commentForm": commentForm,
                "comments": comments,
                "watching": watching
                })

    
    # when the listing itself does not support the POST method
    else:
        return render(request, "auctions/error.html", {
            "code": 405,
            "message": "The POST method is not allowed."
        })
        
        

@login_required(login_url="login")
def close(request, auction_id):
    # checking if the function can handle the POST method only
    if request.method == "POST":
        # checking whether the listing exists
        try:
            # getting the listing/auction by id from the sqlite3 database
            auction = Auction.objects.get(pk=auction_id)

        except Auction.DoesNotExist:
            return render(request, "auctions/error.html", {
                "code": 404,
                "message": "The auction does not exist."
            })

        # checking whether the OU can create a listing
        if request.user != auction.seller:
            messages.error(request, 'The request is not allowed.')
            return HttpResponseRedirect(reverse("listing", args=(auction.id,)))

        else:
            # updating and saving the closed status of a listing
            auction.closed = True
            auction.save()
            
            # a message stating when an OU has sold an item to another OU(highest bidder)
            messages.success(request, 'The auction listing is closed sucessfully.')
            return HttpResponseRedirect(reverse("listing", args=(auction.id,)))

    # if the GET method is not supported   
    else:
        return render(request, "auctions/error.html", {
            "code": 405,
            "message": "The GET method is not allowed."
        })
        

@login_required(login_url="login")
def bid(request, auction_id):  
    # checking if POST method can be handled
    if request.method == "POST":
        # checking whether an auction exists in the database
        try:
            # getting the auction/listing by id(database)
            auction = Auction.objects.get(pk=auction_id)     
            
        except Auction.DoesNotExist:
            return render(request, "auctions/error.html", {
                "code": 404,
                "message": "The auction does not exist."
            })

        # getting the highest bid of the listing
        highest_bid = Bid.objects.filter(auction=auction_id).order_by("-bid_price").first()

        # checking if there is any bid present
        if highest_bid is None:
            highest_bid_price = auction.current_bid
        else:
            highest_bid_price = highest_bid.bid_price

        # creating a form instance with POST data
        form = NewBidForm(request.POST, request.FILES)

        # checking whether the listing is closed or not
        if auction.closed is True:
            messages.error(request, 'The auction listing of this item is closed.')
            return HttpResponseRedirect(reverse("listing", args=(auction.id,))) 
        
        # when the item listing is active
        else:
            # checking whether it's valid
            if form.is_valid():
                # isolating content from the the form data(cleaned)
                bid_price = form.cleaned_data["bid_price"]

                # validating the bid offer, must be greater than current bid
                if bid_price > auction.starting_bid and bid_price > (auction.current_bid or highest_bid_price):
                    # saving the form from a data to a model
                    new_bid = form.save(commit=False)
                    # saving the request user as "bider"
                    new_bid.bider = request.user
                    # getting and saving the auction listing
                    new_bid.auction = auction
                    new_bid.save()

                    # updating and saving the current price of the item
                    auction.current_bid = bid_price
                    auction.save()

                    # returning a message saying it was successful
                    messages.success(request, 'Your Bid offer is made successfully.')

                # handling when an invalid bid offer is entered
                else:
                    #if the bid is invalid, output a proper message
                    messages.error(request, 'Please submit a valid bid offer. Your bid offer must be higher than the starting bid and current price of this item.')

                # if the form is valid, redirect the user to the listing page posted 
                return HttpResponseRedirect(reverse("listing", args=(auction.id,)))    

            else:
                # if the form is invalid, the page will be re-rendered with existing information
                messages.error(request, 'Please submit a valid bid offer. Your bid offer must be higher than the starting bid and current price.')

                # redirecting the user to the listing page
                return HttpResponseRedirect(reverse("listing", args=(auction.id,)))
    
    # when the bid view does not support the get method
    else:
        return render(request, "auctions/error.html", {
            "code": 405,
            "message": "The GET method is not allowed."
        })


@login_required(login_url="login")
def comment(request, auction_id):
    # check on POST method 
    if request.method == "POST":

        # checking if auction listing exists or not
        try:
            # get the auction listing by id from database
            auction = Auction.objects.get(pk=auction_id)     
            
        except Auction.DoesNotExist:
            return render(request, "auctions/error.html", {
                "code": 404,
                "message": "The auction does not exist."
            })
            
        # creating a form instance with the POST data
        form = NewCommentForm(request.POST, request.FILES)

        # checking whether it's valid
        if form.is_valid():
            # saving the comment from the data to the model
            new_comment = form.save(commit=False)
            # saving the ordinary user who leaves a comment, rating, or suspicous warning
            new_comment.user = request.user
            # saving the auction listing for this comment, will populate on the admin interface/ database table
            new_comment.auction = auction
            new_comment.save()

            # returning message stating it was successfully posted
            messages.success(request, 'Your comment was received sucessfully, a SU will respond accordingly.')

            return HttpResponseRedirect(reverse("listing", args=(auction.id,)))
        
        # handling invalid comment forms
        else:
            # if the form is invalid
            messages.error(request, 'Please submit a valid comment.')
     
    # if comment view does not support get method
    else:
        return render(request, "auctions/error.html", {
            "code": 405,
            "message": "The GET method is not allowed."
        })


@login_required(login_url="login")
def addWatchlist(request, auction_id):   
    # checking the POST method 
    if request.method == "POST":
        # checking whether listing exists
        try:
            # getting the auction listing by item id
            auction = Auction.objects.get(pk=auction_id)     
            
        except Auction.DoesNotExist:
            return render(request, "auctions/error.html", {
                "code": 404,
                "message": "The auction does not exist."
            })

        # checking whether the OU has a watchlist
        try:
            watchlist = Watchlist.objects.get(user=request.user)

        except ObjectDoesNotExist:
            # if no watchlist exists,  a watchlist object is created for the Ordinary User
            watchlist = Watchlist.objects.create(user=request.user)
        
        # checking if an item exists in the ordinary user's watchlist
        if Watchlist.objects.filter(user=request.user, auctions=auction):
            messages.error(request, 'You already added in your watchlist')
            return HttpResponseRedirect(reverse("listing", args=(auction.id,)))

        # if the item is not in the watchlist, OU may add it
        watchlist.auctions.add(auction)
            
        # returning message stating it was successfully added
        messages.success(request, 'This item listing has been successfully added to your Watchlist.')

        return HttpResponseRedirect(reverse("listing", args=(auction.id,)))
        
     
    # on the case where addWatchlist view does not support the get method
    else:
        return render(request, "auctions/error.html", {
            "code": 405,
            "message": "The GET method is not allowed."
        })


@login_required(login_url="login")
def removeWatchlist(request, auction_id):   
    # checking the POST method 
    if request.method == "POST":
        # if the auction listing exists
        try:
            # getting the auction listing by its id in the database
            auction = Auction.objects.get(pk=auction_id)     
            
        except Auction.DoesNotExist:
            return render(request, "auctions/error.html", {
                "code": 404,
                "message": "The auction does not exist."
            })
        
        # checking if the item exists in the ordinary user's watchlist
        if Watchlist.objects.filter(user=request.user, auctions=auction):
            # getting the ordinary user's watchlist
            watchlist = Watchlist.objects.get(user=request.user)
           
            # delete the auction from the users watchlist
            watchlist.auctions.remove(auction)
                
            # returning message stating it was successfully removed 
            messages.success(request, 'The item listing has been removed from your watchlist.')

            return HttpResponseRedirect(reverse("listing", args=(auction.id,)))
        
        else:
            # return error message, for this exception
            messages.success(request, 'You cannot remove an item listing that is not in your watchlist.')

            return HttpResponseRedirect(reverse("listing", args=(auction.id,)))
   
     
    # when removeWatchlist view does not support the get method
    else:
        return render(request, "auctions/error.html", {
            "code": 405,
            "message": "The GET method is not allowed."
        })