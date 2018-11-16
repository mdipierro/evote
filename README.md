E-Vote
======

E-Vote is an open source system for secure, trusted, anonymous, and verifiable voting online.  It is based on the [web2py](http://web2py.com/) framework.

Overview
--------

The elections site administrator sets up the election via the web admin interface; setting up the election involves creating a page listing the ballot items (e.g., candidates), and specifying the electorate (the voters, who are represented by email addresses).

Once the election is opened, each voter will receive a unique, non-identifying token by email.  Using that token, the voter visits a corresponding ballot page via their web browser.  One such ballot is created for each voter in the election, and the ballot has its own unique identifier (different from the token received in the email).  Each voter casts their vote using their unique but unidentifiable ballot.  Eventually the election is closed, perhaps manually or perhaps based on a pre-set time, and no more votes can be cast.

While no voter knows any unique ballot identifier other than their own, the election administrators can publish the list of *all* unique identifiers and how they voted.  Each voter can then verify that their own vote was properly recorded, and thus the electorate as a whole can verify the results.

Installing E-Vote
-----------------

E-Vote uses the [web2py](http://web2py.com/) framework and can be installed like any other web2py application; see the web2py documentation for details.  If you just want to try out E-Vote quickly, here is one way to get it up and running on your laptop:

      $ git clone --recursive https://github.com/web2py/web2py.git
      $ cd web2py/applications
      $ git clone https://github.com/mdipierro/evote.git
      $ cd ..
      $ sudo /etc/init.d/apachectl stop  # <-- stop other web server if needed
      $ pip install rsa
      $ python web2py.py
        ...Watch it launch, then visit
           http://127.0.0.1:8000/evote/default/index
        ...in your browser.

To deploy at the root of the site (e.g., at http://127.0.0.1:8000/ instead of http://127.0.0.1:8000/evote/default/index), simply name the E-Vote directory `applications/init/` instead of `applications/evote/`.  The magic name "init" will cause E-Vote to appear at the site root.

To deploy E-Vote in production, you may want to go to [web2py.com](http://web2py.com) and learn more about deploying web2py-based applications in general.  If you're in a hurry, see `scripts/setup-*.sh` in the web2py tree.  One common way to deploy web2py applications is with WSGI under Apache HTTPD: in the web2py tree, copy `handlers/wsgihandler.py` to the top level of the tree, and set the appropriate WSGI options in the Apache configuration.  See the [Deployment recipes](http://web2py.com/book/default/chapter/13) chapter in the web2py manual for more.

Administrating E-Vote
---------------------

Let's assume you installed E-vote as site root, in `applications/init/`.

When you first launched the web server ('python web2py.py' in the above example), you were prompted to set an admin password.  That password allows you to log in on the web2py administration console:

      http://127.0.0.1:8000/admin/

(If you plan to run in production under Apache HTTPD or some other web server, then one easy way to set the admin password is to run web2py once first under its own web server as per above, just to set the admin password, then shut it down and switch to running it with your production web server thereafter.)

That URL will redirect to http://127.0.0.1:8000/admin/default/site, which will list the installed applications, of which "init" will be one.  That's E-Vote.  Pull down the "Manage" menu and select "Edit" -- you will see a web2py admin console for this application.

Under most circumstances, you won't need to do anything here; creating elections and running them does not require customization of the E-Vote app.  Instead, see "Registering Users and Running Elections" later on.

Customizing E-Vote's Appearance
-------------------------------

(Again, this somewhat duplicates web2py documentation, but since E-Vote users are most likely to want to customize their election sites' front pages and make other basic changes, we cover that here.)

We again assume you installed in the site root, as `applications/init/`.

Your site's pages live in init/views/default/.  For example, the front page is init/views/default/index.html.  These view files are mostly written in HTML, but they contain occasional Python and template code embedded between double curly braces, e.g., "{{extend 'layout.html'}}". See [web2py.com/books/default/chapter/29/05/the-views](http://web2py.com/books/default/chapter/29/05/the-viewshttp://web2py.com/books/default/chapter/29/05/the-views) for more about views and the templating commands available.

Registering Users and Running Elections
----------------------------------------

We cover the topics of registering users and running elections together, because they are somewhat intertwined.

In a normal E-Vote deployment, anyone can create their own user account by going to the front page, pulling down the "Login" menu on the upper right, and choosing "Register".  After entering some information that includes their email address and a password of their choice, they will be sent an email with a unique link.  To confirm the registration, they visit that link and enter their email addres and password.  Now that user account exists.  (See "Testing E-Vote Without Email" below for how to try all this without involving a mail delivery system.)

Now that we've created the user, what can she do?

A user can create new elections, and vote in elections where she has been named as a voter.

This may sound surprising -- after all, one might imagine that there is a single E-Vote administrator (perhaps the person who knows the initial admin password mentioned earlier in "Administrating E-Vote") who sets up elections, and who is separate from the voters who vote in those elections.  But that's not how E-Vote works.  Instead, anyone with an account can set up an election, assuming they have the "is_manager" flag set on their account, which is something they themselves can set when they register the account, or can change later by pulling down the the upper right user menu and clicking on "Profile" to manager their account (try it!).

So let's set up an election.  After making sure your "is_manager" flag is turned on, choose "Elections" from the nav bar at the top, then click the `New Election` button under "Create a election."

You'll see a ballot creation form, which should be self-explanatory.  Edit it to look like the ballot you want voters to see.  Then put the email addresses of all those voters in the `Voters` box, one per line (those voters will receive unique tokens by email that allow them to vote in this election).  If there's anyone else you want able to manage this election, add them to the "Managers" box.

Click `Save and Preview` to be brought to a preview page where you can make sure the ballot looks exactly as you want the voters to see it.  Test it out -- in particular, if you are doing any ranked-choice elections, try dragging those candidates up and down and make sure the text above that group informs voters that they can drag to reorder.

Once you're satisfied, go to the top of the page and click `Email Voters and Start Election Now`.  This will cause the ballot emails to go out to voters.

Concluding Elections
--------------------

An election closes either on the date that was specified, if any, when the election was set up, or when one of the election's managers manually closes it from their Elections administration page (click on "Elections" in the nav bar).

When you close an election, will see a results page such as

      http://hostname_or_ip_etc.com/init/default/results/6

(You or any voter can also visit that page at any time, by choosing "Results" from the `Action` menu next to that election on the Elections page.)

The results are mostly self-explanatory, except for the ranked-choice groups, which use single-letter codes to indicate the candidate's scores under various scoring algorithms.  For example, you might see this (well, in a very unusual election that happened to have just one voter):

      M:3  I:1  S:1       Candidate A
      M:9  I:1  S:2       Candidate B
      M:1  I:1  S:0       Candidate C

Here's how to interpret those codes:

      M = Borda (exponential)   I = Instant Runoff      S = Schulze
      -----------------------   ------------------      -------------------
      M:3                       I:1                     S:1
      M:9                       I:1                     S:2
      M:1                       I:1                     S:0

M = Borda Method = https://en.wikipedia.org/wiki/Borda_count

I = Instant Runoff = https://en.wikipedia.org/wiki/Instant-runoff_voting

S = Schulze Method = https://en.wikipedia.org/wiki/Schulze_method

(Yes, we plan to improve the results interface.)

Testing E-Vote Without Email
----------------------------

If you'd like to test all this out without worrying about email-sending configuration, you can edit this line in `models/0.py`:

      EMAIL_SERVER = 'localhost'

Change "localhost" to "logging"...

      EMAIL_SERVER = 'logging'   # 'localhost'

...and now the emails will print out on the web server console instead of being sent.  You'll see things like this on the console:

      Welcome jrandom@example.com!  Click on the link
      http://hostname_or_ip_etc.com/init/default/user/verify_email/18b9f977-249f-45e8-93fe-59161a687f88 
      to verify your email
