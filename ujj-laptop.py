import os
from google.appengine.ext.webapp import template

import cgi
import time

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from datetime import date


class Content(db.Model):
    title = db.StringProperty()
    text = db.TextProperty()
    content_id = db.IntegerProperty()
    type = db.StringProperty()
    summary = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)  

class ContentTags(db.Model): 
    content_id = db.IntegerProperty()
    tag = db.StringProperty()	

class Blog(webapp.RequestHandler):
    def get(self):
	content_query = Content.all()	
	tags_query = ContentTags.all()
	pid = self.request.get('i')
	edit = self.request.get('e')
        show_new_form = None
        greeting = None
        if edit:
            user = users.get_current_user()
            if user:
                if users.is_current_user_admin():
                    greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                                (user.nickname(), users.create_logout_url("/")))
                    show_new_form = 1           
                else:
                    greeting = (" Not an admin (<a href=\"%s\">sign out</a>)" %
                                (users.create_logout_url("/")))
            else:
                greeting = ("<a href=\"%s\">Sign in</a>." %
                            users.create_login_url("/"))

        bookmark = self.request.get('bookmark')
        cat = self.request.get('c')
        next = None
	if (pid):
		content_query.filter("content_id =",int(pid))
		post = content_query.fetch(1)
		tags_query.filter("content_id =",int(pid))
		tags = tags_query.fetch(5)
		tagstr = ""
		for tag in tags:
			if tagstr != "":			
				tagstr = tagstr + "," + tag.tag
			else:
				tagstr = tag.tag
		#publish_date = date.fromtimestamp(time.time())
		publish_date = dict()
		publish_date['year'] = post[0].date.year
		publish_date['day'] = post[0].date.day 
		publish_date['month'] = post[0].date.month  
		template_values = { 'post': post, 'single': 1, 'tags' : tagstr, 'show_new_form': show_new_form, 'greeting':greeting, 'publish_date':publish_date}
	else:
                if bookmark:         
                    content_query.filter("content_id <=", int(bookmark))
                if cat:
                    content_query.filter("type =",cat)
		content_query.order('-content_id')
                posts = content_query.fetch(PAGESIZE + 1)
		if len(posts) == PAGESIZE + 1:     
                    next = posts[-1].content_id              
                posts = posts[:PAGESIZE]    
		template_values = { 'posts' : posts, 'next' : next, 'cat' : cat }
	if (edit):
		path = os.path.join(os.path.dirname(__file__), 'base_edit.html')
	else:
        	path = os.path.join(os.path.dirname(__file__), 'base_blog.html')
        self.response.out.write(template.render(path, template_values))


class PublishFeed(webapp.RequestHandler):
    def get(self):
	content_query = Content.all()	
        cat = self.request.get('c')
        if cat:
            content_query.filter("type =",cat)
	content_query.order('-content_id')
        posts = content_query.fetch(PAGESIZE)
	template_values = { 'posts' : posts, 'cat' : cat }
       	path = os.path.join(os.path.dirname(__file__), 'base_feed.html')
        self.response.out.write(template.render(path, template_values))

            
class PublishPost(webapp.RequestHandler):
    def post(self):
        title = self.request.get('title')
        content = self.request.get('content')
        ptype = self.request.get('type')
	summary = self.request.get('summary')
	tagstr = self.request.get('tags')
	content_id_str = self.request.get('i')
	content_id = 0
        if content_id_str:
                content_id = int(content_id_str)
	if (content_id):
		content_query = Content.all()	
		content_query.filter("content_id =",content_id)
		post = content_query.fetch(1)
		if post:
			post[0].title = title
		        post[0].text = content
		        post[0].type = ptype
			post[0].summary = summary
			post[0].put()
	else:
		post = Content()
	        post.title = title
	        post.text = content
	        post.type = ptype
		post.summary = summary
		post.put()
        	content_id = post.key().id()
	        post.content_id = int(content_id)
       		post.put()
	if (tagstr):
		tags = tagstr.split(",")
		for tag in tags:		
			tagged = ContentTags()
			tagged.tag = tag
			tagged.content_id = content_id
			tagged.put()		
        status = "\m/ success"	    	 
        template_values = {
		  'status': status,
		  'content_id': content_id,	
		  }
        path = os.path.join(os.path.dirname(__file__), 'base_posted.html')
        self.response.out.write(template.render(path, template_values))


class New(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        show_new_form = None
        if user:
            if users.is_current_user_admin():
                greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                        (user.nickname(), users.create_logout_url("/")))
                show_new_form = 1           
            else:
                greeting = (" Not an admin (<a href=\"%s\">sign out</a>)" %
                        (users.create_logout_url("/")))
        else:
            greeting = ("<a href=\"%s\">Sign in</a>." %
                        users.create_login_url("/"))
        template_values = {'greeting': greeting, 'show_new_form' : show_new_form}
   	path = os.path.join(os.path.dirname(__file__), 'base_new.html')
	self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication([('/', Blog),
				      ('/new', New),
				      ('/post', PublishPost),	
                                      ('/feed', PublishFeed),
				      ('/edit', Blog),],debug=True)


PAGESIZE = 5

def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
