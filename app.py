#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config
from flask_migrate import Migrate
import sys
from sqlalchemy.sql import func
import datetime
from models import app, db, Venue, Artist, Show


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config.from_object('config')
moment = Moment(app)
db.init_app(app)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
''' newData = Venue.query.order_by('id').join(Show, isouter=True).all()
for i in newData:
    print(i.name, ' ', i.shows) '''


@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    venues_list = Venue.query.order_by('id').all()
    final_list = []
    for venue in venues_list:
        matchingDict = next((i for i, item in enumerate(
            final_list) if item['city'] == venue.city and item['state'] == venue.state), False)
        venueDate = {
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': Show.query.filter(Show.venue_id == venue.id, Show.start_time > datetime.datetime.now()).count()
        }
        if matchingDict:
            final_list[matchingDict]['venues'].append(venueDate)
        else:
            final_list.append({
                'city': venue.city,
                'state': venue.state,
                'venues': [venueDate]
            })

    return render_template('pages/venues.html', areas=final_list)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    foundVenues = Venue.query.filter(
        Venue.name.ilike(f'%{search_term}%'))

    def mapF(venue):
        return {
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': Show.query.filter(Show.venue_id == venue.id, Show.start_time > datetime.datetime.now()).count()
        }
    foundVenuesMapped = list(map(mapF, foundVenues))
    response = {
        "count": foundVenues.count(),
        "data": foundVenuesMapped
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    ven = Venue.query.get(venue_id)
    venShows = Show.query.filter(Show.venue_id == venue_id)
    pastShows = list(filter(lambda show: show.start_time <
                            datetime.datetime.now(), venShows))
    upcomingShows = list(
        filter(lambda show: show.start_time > datetime.datetime.now(), venShows))

    def mapShow(show):
        return {
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        }
    data = {
        'id': venue_id,
        'name': ven.name,
        'genres': ven.genres,
        'address': ven.address,
        'city': ven.city,
        'state': ven.state,
        'phone': ven.phone,
        'website': ven.website,
        'facebook_link': ven.facebook_link,
        'seeking_talent': ven.seeking_talent,
        'seeking_description': ven.seeking_description,
        'image_link': ven.image_link,
        'past_shows': list(map(mapShow, pastShows)),
        'upcoming_shows': list(map(mapShow, upcomingShows)),
        "past_shows_count": len(pastShows),
        "upcoming_shows_count": len(upcomingShows),
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    formData = request.form
    try:
        newVenue = Venue(name=formData['name'], city=formData['city'], state=formData['state'], address=formData['address'],
                         phone=formData['phone'], genres=formData['genres'], facebook_link=formData['facebook_link'],
                         image_link=formData['image_link'], website=formData[
                             'website'], seeking_talent=True if formData['seeking_talent'] == 'True' else False,
                         seeking_description=formData['seeking_description'])
        db.session.add(newVenue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + formData['name'] + ' was successfully listed!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        db.session.rollback()
        flash('An error occurred. Venue ' +
              formData['name'] + ' could not be listed.')
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        ven = Venue.query.get(venue_id)
        ven.delete()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    foundArtists = Artist.query.filter(
        Artist.name.ilike(f'%{search_term}%'))

    def mapF(artist):
        return {
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': Show.query.filter(Show.artist_id == artist.id, Show.start_time > datetime.datetime.now()).count()
        }
    foundArtistsMapped = list(map(mapF, foundArtists))
    response = {
        "count": foundArtists.count(),
        "data": foundArtistsMapped
    }
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    art = Artist.query.get(artist_id)
    artShows = Show.query.filter(Show.artist_id == artist_id)
    pastShows = list(filter(lambda show: show.start_time <
                            datetime.datetime.now(), artShows))
    upcomingShows = list(
        filter(lambda show: show.start_time > datetime.datetime.now(), artShows))

    def mapShow(show):
        return {
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": str(show.start_time)
        }
    data = {
        'id': artist_id,
        'name': art.name,
        'genres': art.genres,
        'city': art.city,
        'state': art.state,
        'phone': art.phone,
        'website': art.website,
        'facebook_link': art.facebook_link,
        'seeking_venue': art.seeking_venue,
        'seeking_description': art.seeking_description,
        'image_link': art.image_link,
        'past_shows': list(map(mapShow, pastShows)),
        'upcoming_shows': list(map(mapShow, upcomingShows)),
        "past_shows_count": len(pastShows),
        "upcoming_shows_count": len(upcomingShows),
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    # TODO: populate form with fields from artist with ID <artist_id>
    artist = Artist.query.get(artist_id)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    formData = request.form
    art = Artist.query.get(artist_id)
    art.name = formData['name']
    art.city = formData['city']
    art.state = formData['state']
    art.phone = formData['phone']
    art.genres = formData['genres']
    art.facebook_link = formData['facebook_link']
    art.image_link = formData['image_link']
    art.seeking_venue = True if formData['seeking_venue'] == 'True' else False
    art.website = formData['website']
    art.seeking_description = formData['seeking_description']

    try:
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    # TODO: populate form with values from venue with ID <venue_id>
    venue = Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    formData = request.form
    venue = Venue.query.get(venue_id)
    venue.name = formData['name']
    venue.city = formData['city']
    venue.state = formData['state']
    venue.address = formData['address']
    venue.phone = formData['phone']
    venue.genres = formData['genres']
    venue.facebook_link = formData['facebook_link']
    venue.image_link = formData['image_link']
    venue.seeking_talent = True if formData['seeking_talent'] == 'True' else False
    venue.website = formData['website']
    venue.seeking_description = formData['seeking_description']
    try:
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    formData = request.form
    try:
        new_artist = Artist(name=formData['name'], city=formData['city'], state=formData['state'],
                            phone=formData['phone'], genres=formData['genres'], facebook_link=formData[
                                'facebook_link'], image_link=formData['image_link'],
                            website=formData['website'], seeking_venue=True if formData['seeking_venue'] == 'True' else False,
                            seeking_description=formData['seeking_description'])
        db.session.add(new_artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    shows = Show.query.join(Artist).join(Venue).all()
    data = []
    for item in shows:
        data.append({
            'venue_id': item.venue.id,
            'venue_name': item.venue.name,
            'artist_id': item.artist.id,
            'artist_name': item.artist.name,
            'artist_image_link': item.artist.image_link,
            'start_time': str(item.start_time)
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    formData = request.form
    try:
        new_show = Show(
            venue_id=formData['venue_id'], artist_id=formData['artist_id'], start_time=formData['start_time'])
        db.session.add(new_show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('An error occurred. Show could not be listed.')
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
