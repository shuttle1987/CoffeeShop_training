"""
Views for the actual coffee shops
"""
import os.path

from flask import render_template, Blueprint, redirect, current_app, request, flash, url_for
from flask_security import login_required, current_user
from sqlalchemy import func

from coffeeshop.server import db
from .forms import ShopForm, ReviewForm
from .utils import secure_filename, upload_file_to_s3
from .models import Shop, Review

coffee_blueprint = Blueprint("coffee", __name__)


@coffee_blueprint.route('/shop/<int:id>')
def shops(id):
    shop = Shop.query.get(id)
    review_comments = filter(lambda r: r.comment, shop.reviews)
    return render_template('shop/shop_details.html', shop=shop)


@coffee_blueprint.route('/shop/add', methods=['GET', 'POST'])
@login_required
def add_shop():
    form = ShopForm()
    if form.validate_on_submit():

        shop_name = form.name.data
        address = form.address.data
        url = form.url.data

        latitude = form.latitude.data
        longitude = form.longitude.data
        current_app.logger.debug(f'{latitude} {longitude}')

        geom = None
        if latitude and longitude:
            geom = f'POINT ({longitude} {latitude})'

        photo = None
        f = form.photo.data
        if f:
            f.filename = secure_filename(f.filename)
            photo = upload_file_to_s3(f)

        shop = Shop(name=shop_name, address=address, url=url, photo=photo, location=geom, user=current_user)
        db.session.add(shop)
        db.session.commit()
        current_app.logger.info(f'Created new {shop}')

        return redirect(f'/shop/{shop.id}')
    return render_template('shop/create.html', form=form)


@coffee_blueprint.route('/shop/search')
@login_required
def search_shop():
    pass


@coffee_blueprint.route('/review/add', methods=['GET', 'POST'])
@login_required
def add_review():
    form = ReviewForm()
    if form.validate_on_submit():
        shop = Shop.query.get(int(form.shop_id.data))
        rating = form.rating.data
        comment = form.comment.data or None

        review = Review(rating=rating, comment=comment, shop=shop, user=current_user)
        db.session.add(review)
        db.session.commit()
        current_app.logger.info(f'Created new {review}')

        return redirect(f'/shop/{shop.id}')

    try:
        shop_id = request.args['shop_id']
    except KeyError:
        flash('You need to have a shop to review!')
        return redirect(url_for('coffee.search_shop'))

    shop = Shop.query.get(shop_id)
    return render_template('shop/add_review.html', shop=shop, form=form)


