E-Vote
======

E-Vote is an open source system for secure, trusted, anonymous, and verifiable voting online.  It is based on the [web2py](http://web2py.com/) framework.

Overview
--------

The elections site administrator sets up the election via the web admin interface; setting up the election involves creating a page listing the ballot items (e.g., candidates), and specifying the electorate (the voters, who are represented by email addresses).

Once the election is opened, each voter will receive a unique, non-identifying token by email.  Using that token, the voter visits a corresponding ballot page in their web browser -- one such ballot is created for each voter in the election.  The voter casts their vote. Eventually the election closes, based on a pre-set time, and no more votes can be cast.

While no voter knows any unique token other than their own, by publishing the list of *all* unique tokens and how they voted, each voter can verify that their vote was properly recorded, and the electorate as a whole can verify that the expected set of people voted.

Installing E-Vote
-----------------

E-Vote uses the [web2py](http://web2py.com/) framework and can be installed like any other web2py application; see the web2py documentation for details.  If you just want to try out E-Vote quickly, here is one way to get it up and running on your laptop:

      $ git clone https://github.com/web2py/web2py.git
      $ cd web2py/applications
      $ git clone https://github.com/mdipierro/evote.git
      $ cd ..
      $ sudo /etc/init.d/apachectl stop  # <-- stop other web server if needed
      $ python web2py.py
        ...Watch it launch, then visit
           http://127.0.0.1:8000/evote/default/index
        ...in your browser.

To deploy at the root of the site (e.g., at http://127.0.0.1:8000/ instead of http://127.0.0.1:8000/evote/default/index), simply name the E-Vote directory applications/init/ instead of applications/evote/.  The magic name "init" will cause E-Vote to appear at the site root.

(To really deploy E-Vote in production, go to web2py.com and learn about deploying web2py-based applications in general, of course.)

Administrating E-Vote
---------------------

Let's assume you installed E-vote as site root, in applications/init/.

When you first launched the web server ('python web2py.py' in the above example), you were prompted to set an admin password.  That password allows you to log in on the web2py administration console:

      http://127.0.0.1:8000/admin/

(If you're running in production under Apache HTTPD or some other web server, then you set the admin password already by other means.)

That will redirect to http://127.0.0.1:8000/admin/default/site, which will list the installed applications, of which "init" will be one. That's E-Vote.  Pull down the "Manage" menu and select "Edit" -- you will see a web2py admin console for this application.

Customizing E-Vote
------------------

(Again, this somewhat duplicates web2py documentation, but since E-Vote users are likely to want to customize their election sites' front pages and make other basic changes, we cover that below.)

We again assume you installed in the site root, as applications/init/.

Your site's pages live in init/views/default/.  For example, the front page is init/views/default/index.html.  These view files are mostly written in HTML, but they contain occasional Python and template code embedded between double curly braces, e.g., "{{extend 'layout.html'}}". See [web2py.com/books/default/chapter/29/05/the-views](http://web2py.com/books/default/chapter/29/05/the-viewshttp://web2py.com/books/default/chapter/29/05/the-views) for more about views and the templating commands available.
