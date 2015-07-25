import utilities

# -------------------------------------------------------------------------------
@auth.requires_login()
def index():
    return dict()

# -------------------------------------------------------------------------------
def get_dates():

    if len(request.args) < 1:
        if session.handle:
            handle = str(session.handle)
        else:
            redirect(URL("default", "submissions"))
    else:
        handle = str(request.args[0])

    stable = db.submission

    row = db.executesql("SELECT status, time_stamp, COUNT(*) FROM submission WHERE submission.stopstalk_handle='" + handle + "' GROUP BY DATE(submission.time_stamp), submission.status;")

    total_submissions = {}
    for i in row:
        sub_date = str(i[1]).split()[0]
        if total_submissions.has_key(sub_date):
            total_submissions[sub_date][i[0]] = i[2]
            total_submissions[sub_date]["count"] += i[2]
        else:
            total_submissions[sub_date] = {}
            total_submissions[sub_date][i[0]] = i[2]
            total_submissions[sub_date]["count"] = i[2]

    return dict(total=total_submissions)

# -------------------------------------------------------------------------------
def get_stats():
    """
        Current Implementation:
        Logged in user can see only his profile
    """

    if request.extension != "json":
        redirect(URL("default", "index"))

    if len(request.args) < 1:
        if session.handle:
            handle = str(session.handle)
        else:
            redirect(URL("default", "index"))
    else:
        handle = str(request.args[0])

    stable = db.submission
    count = stable.id.count()
    row = db(stable.stopstalk_handle == handle).select(stable.status, count,
                                                       groupby=stable.status)
    return dict(row=row)

# -------------------------------------------------------------------------------
def profile():
    """
        @ToDo: Prettify the page ;)
    """
    return dict()

# -------------------------------------------------------------------------------
@auth.requires_login()
def submissions():
    utilities.retrieve_submissions(session.user_id)
    submissions = db(db.submission.user_id == session.user_id).select(orderby=~db.submission.time_stamp)
    table = utilities.render_table(submissions)        
    return dict(table=table)

# -------------------------------------------------------------------------------
@auth.requires_login()
def notifications():
    return locals()

# -------------------------------------------------------------------------------
@auth.requires_login()
def friend_requests():

    rows = db(db.friend_requests.to_h == session.user_id).select()
    table = TABLE(_class="table")
    table.append(TR(TH(T("Name")),
                    TH(T("Institute")),
                    TH(T("Action"))))

    for row in rows:
        tr = TR()
        tr.append(TD(row.from_h.first_name + " " + row.from_h.last_name))
        tr.append(TD(row.from_h.institute))
        tr.append(TD(FORM(INPUT(_value="Accept", _type="submit"),
                          _action=URL("user", "accept_fr", args=[row.from_h, row.id])),
                     FORM(INPUT(_value="Reject", _type="submit"),
                          _action=URL("user", "reject_fr", args=[row.id])),
                     ))
        table.append(tr)
    return dict(table=table)

# -------------------------------------------------------------------------------
@auth.requires_login()
def add_friend(user_id, friend_id):

    user_friends = db(db.friends.user_id == user_id).select(db.friends.friends_list).first()
    user_friends = eval(user_friends["friends_list"])
    user_friends.add(friend_id)
    db(db.friends.user_id == user_id).update(friends_list=str(user_friends))

# -------------------------------------------------------------------------------
@auth.requires_login()
def accept_fr():
    if len(request.args) < 2:
        redirect(URL("user", "friend_requests"))

    friend_id = int(request.args[0])
    row_id = int(request.args[1])
    user_id = session.user_id

    # Add friend ID to user's friends list
    add_friend(user_id, friend_id)

    # Add user ID to friend's friends list
    add_friend(friend_id, user_id)
    
    # Delete the friend request row
    db(db.friend_requests.id == row_id).delete()

    redirect(URL("user", "friend_requests"))
    return locals()
    
# -------------------------------------------------------------------------------
@auth.requires_login()
def reject_fr():

    if request.args == []:
        redirect(URL("user", "friend_requests"))

    fr_id = request.args[0]

    # Simply delete the friend request
    db(db.friend_requests.id == fr_id).delete()
    redirect(URL("user", "friend_requests"))
    return locals()

# -------------------------------------------------------------------------------
@auth.requires_login()
def custom_friend():

    list_fields = ["first_name",
                   "last_name",
                   "institute",
                   "stopstalk_handle",
                   "codechef_handle",
                   "codeforces_handle",
                   "spoj_handle"]

    form = SQLFORM(db.custom_friend,
                   fields=list_fields,
                   hidden=dict(user_id=session.user_id))

    # Set the hidden field
    form.vars.user_id = session.user_id
    form.process()

    if form.accepted:
        session.flash = "Submissions for custom user added"
        utilities.retrieve_submissions(form.vars.id, True)
        redirect(URL("default", "index"))
    return dict(form=form)
