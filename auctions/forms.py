from django.forms import ModelForm
from django import forms
from .models import Auction, Bid, Comment 

# creatinf a new auction listing model form class using Django Form
class NewListingForm(ModelForm):
    # specifiying the name of a model to use
    class Meta:
        model = Auction
        fields = ["title", "description", "starting_bid", "category", "imageURL"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                        "placeholder": "Enter the title of your item listing",
                        "class": "form-control"
                    }
            ),
            "description": forms.Textarea(
                attrs={
                        "placeholder": "Enter a description of the item to be sold",
                        "class": "form-control",
                        "rows": 15
                    }
            ),
            "starting_bid": forms.NumberInput(
                attrs={'class': 'form-control'}
                ),
            "imageURL": forms.URLInput(
                attrs={
                    'class': 'form-control',
                    "placeholder": "Enter the URL of the desired image",
                    }
                ) 
        }

# creating a class for a new Bid model form 
class NewBidForm(ModelForm):
    # specifing the name of the model to use
    class Meta:
        model = Bid
        fields = ["bid_price"]

# creating a class for a new Comment model form
class NewCommentForm(ModelForm):
    # sepcifit the name of model to use
    class Meta:
        model = Comment
        fields = ["headline", "message"]
        widgets = {
            "headline": forms.TextInput(
                attrs={
                        "placeholder": "Enter a rating from 1-5; Enter 0 if reporting stolen or just leaving comment. ",
                        "class": "form-control"
                    }
            ),
            "message": forms.Textarea(
                attrs={
                        "placeholder": "Report this item as suspicious (will be reviewed by SU) or you may otherwise leave a comment",
                        "class": "form-control",
                        "rows": 4
                    }
        )}

