import logging
from datetime import datetime
from datetime import timedelta
import pkg_resources

from pyramid.httpexceptions import HTTPFound
from pyramid.exceptions import NotFound
from pyramid.url import route_url
from pyramid.renderers import render_to_response

from pyramid_handlers import action
from pylonshq.handlers.base import BaseHandler as base

from beaker.cache import cache_region

log = logging.getLogger(__name__)

        
class PageHandler(base):
    
    def render_page(self, section, redir_elems):
        endpath = self.request.matchdict.get('endpath', None)
        if not endpath:
            return HTTPFound(
                location=route_url(
                    'subsections',
                    self.request,
                    action=section,
                    endpath='/'.join(redir_elems)
                )
            )
        tmpl_path = 'templates/pages/%s/%s.mako' % (
            section,
            '/'.join(endpath)
        )
        if pkg_resources.resource_exists('pylonshq', tmpl_path):
            self.c.active_footer_nav = '-'.join(
                [self.request.matchdict.get('action')]
                +list(endpath)
            )
            values = {}
            return render_to_response(
                'pylonshq:%s' % tmpl_path, values, self.request)
        raise NotFound()
    
    @action(renderer='pylonshq:templates/home/home.mako')
    def index(self):
        self.c.pagename = 'Home'
        @cache_region('moderate_term')
        def latest_discussions():
            import feedparser
            d = feedparser.parse(
                'http://groups.google.com/group/pylons-discuss/feed/atom_v1_0_msgs.xml'
            )
            entries = [dict(
                title = entry.title,
                link = entry.link,
                author = entry.author_detail.name,
                updated = (
                    datetime(*entry.updated_parsed[:6])-timedelta(hours=5)
                ).strftime('%b %d, %H:%M')
            ) for entry in d['entries']]
            return entries
        @cache_region('default_term')
        def latest_projects():
            from operator import attrgetter
            github = self.request.registry.get('github')
            all_projects = github.repos.list(
                self.request.registry.settings.get('github.username')
            )
            ordered = sorted(
                (project for project in all_projects),
                key=attrgetter('pushed_at'),
                reverse=True
            )
            return [ordered[i] for i in xrange(15)]
        return {
            'discussions': latest_discussions(),
            'projects': latest_projects()
        }
    
    @action()
    def pylons(self):
        self.c.pagename = 'Pylons Project'
        return self.render_page('pylons', ('about',))
    
    @action()
    def projects(self):
        self.c.pagename = 'Projects'
        endpath = self.request.matchdict.get('endpath')
        if endpath is not None:
            if 'pyramid' in endpath:
                self.c.masthead_logo = 'pyramid'
            elif 'pylons-framework' in endpath:
                self.c.masthead_logo = 'pylonsfw'
        return self.render_page('projects', ('pyramid','about',))
    
    @action()
    def community(self):
        self.c.pagename = 'Community'
        return self.render_page('community', ('how-to-participate',))
    
    @action()
    def tools(self):
        self.c.pagename = 'Tools'
        return self.render_page('tools', ('pastebins',))
        
    @action(renderer='pylonshq:templates/home/test.mako')
    def test(self):
        self.c.pagename = 'Test'
        hello = self.request.translate('Hello')
        print hello
        return {}
