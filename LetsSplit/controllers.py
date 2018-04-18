from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug import secure_filename
from datetime import datetime
import os
from models import DB, users, friends, transactions, groups, group_transactions


app_blueprint = Blueprint('app_blueprint', __name__)


@app_blueprint.route('/', methods = ['GET', 'POST'])
def sign_up(message=None):
    if request.method == 'POST':
        if 'SignUp' in request.form:
            if not request.form['email'] or not request.form['username'] or not request.form['password'] or not request.form['DOB'] or not request.form['passwordconfirm']:
                flash('Please enter all the fields', 'error')
            else:
                x = users.query.filter_by(username=request.form['username']).first()
                if request.form['password'] != request.form['passwordconfirm']:
                    message = 'Passwords Don\'t Match'
                if x is None:
                    img = request.files['profile_pic']
                    img.save(secure_filename(img.filename))
                    os.system("mv " + secure_filename(img.filename) + " ./static/")
                    user = users(email = request.form['email'], username = request.form['username'], password = request.form['password'], DOB = request.form['DOB'], profile_pic_url = secure_filename(img.filename), name = request.form['name'], bio = request.form['bio'])
                    user_friends = friends(username=request.form['username'])
                    DB.session.add(user)
                    DB.session.add(user_friends)
                    DB.session.commit()
                    return redirect(url_for('app_blueprint.profile_page', username=request.form['username']))
                else:
                    message = 'Username already taken'

        elif 'SignIn' in request.form:
            if request.form['username'] is '':
                message = "Please Enter Username"
            elif not request.form['password']:
                message = "Please Enter Password"
            else :
                x = users.query.filter_by(username=request.form['username']).first()
                if x is None:
                    message = "Incorrect Username"
                elif request.form['password'] is None:
                    message = 'Please Enter Password'
                elif str(x.password) == str(request.form['password']) and x is not None:
                    return redirect(url_for('app_blueprint.profile_page', username=request.form['username']))
                elif str(x.password) != str(request.form['password']):
                    message = "Incorrect Password"

    return render_template('home.html', message=message)


@app_blueprint.route('/<username>', methods=['GET', 'POST'])
def profile_page(username, message=None):
    user = users.query.filter_by(username=username).first()
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'add_transaction' in request.form:
            if request.form['from_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['from_user']).first()
                friend_list = x.friend.split(',')
                if request.form['to_user'] not in friend_list:
                    message = request.form['to_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            elif request.form['to_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['to_user']).first()
                friend_list = x.friend.split(',')
                if request.form['from_user'] not in friend_list:
                    message = request.form['from_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')                    
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            else:
                message = "You can only add your own transactions"
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'settle' in request.form:
            transaction = transactions.query.get(request.form['primary_id'])
            transaction.settled = "1"
            date_settled = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
            transaction.date_settled = date_settled                  
            DB.session.commit()
        if 'comment_add' in request.form:
            x = transactions.query.get(request.form['transaction_id'])
            print(request.form['transaction_id'])
            print(x)
            x.comments = x.comments + ',' + request.form['submitting_user'] + ' ' + request.form['comment']
            DB.session.commit()
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))        

    to_list = transactions.query.filter_by(from_user=username).all()
    from_list = transactions.query.filter_by(to_user=username).all()

    return render_template('profile_page.html', username=username, user=user, message=message, to_list=to_list, from_list=from_list)


@app_blueprint.route('/<username>/search/<query>', methods=['GET', 'POST'])
def search_results(username, query, message=None):
    url_dict = {}
    friend_list = []
    fr1 = friends.query.filter_by(username=username).first()
    friend_list = fr1.friend.split(',')
    results = users.query.filter(users.username.startswith(query)).all()
    for res in results:
        if res.username == username:
            results.remove(res)
            break
    for x in results:
        url_dict[x.username] = x.profile_pic
    if not results:
        message = "Oops... No results found"
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'add_friend' in request.form:
            fr2 = friends.query.filter_by(username=request.form['friend_to_be_added']).first()
            a = fr2.friend
            z = fr1.friend
            fr1.friend = z + request.form['friend_to_be_added'] + ','
            fr2.friend = a + username + ','
            friend_list = fr1.friend.split(',')
            DB.session.commit()
        if 'add_transaction' in request.form:
            if request.form['from_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['from_user']).first()
                friend_list = x.friend.split(',')
                if request.form['to_user'] not in friend_list:
                    message = request.form['to_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')                                        
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled=False, date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            elif request.form['to_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['to_user']).first()
                friend_list = x.friend.split(',')
                if request.form['from_user'] not in friend_list:
                    message = request.form['from_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')                                        
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled=False, date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            else:
                message = "You can only add your own transactions"
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username)) 
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))

    return render_template('search_results.html', username=username, results=results, message=message, profile_pic_dict=url_dict, friend_list=friend_list)


@app_blueprint.route('/<username>/history', methods=['GET', 'POST'])
def log(username, message=None):
    user = users.query.filter_by(username=username).first()
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'add_transaction' in request.form:
            if request.form['from_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['from_user']).first()
                friend_list = x.friend.split(',')
                if request.form['to_user'] not in friend_list:
                    message = request.form['to_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')                                        
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            elif request.form['to_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['to_user']).first()
                friend_list = x.friend.split(',')
                if request.form['from_user'] not in friend_list:
                    message = request.form['from_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')                                        
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            else:
                message = "You can only add your own transactions"
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'comment_add' in request.form:
            x = transactions.query.get(request.form['transaction_id'])
            print(request.form['transaction_id'])
            print(x)
            x.comments = x.comments + ',' + request.form['submitting_user'] + ' ' + request.form['comment']
            DB.session.commit()
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username)) 

    to_list = transactions.query.filter_by(from_user=username).all()
    from_list = transactions.query.filter_by(to_user=username).all()

    return render_template('log.html', username=username, user=user, to_list=to_list, from_list=from_list, message=message)


@app_blueprint.route('/<username>/search/<query>/profile', methods = ['GET', 'POST'])
def open_else_profile(username, query, message=None):
    query_user = users.query.filter_by(username=query).first()
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'settle' in request.form:
            transaction = transactions.query.get(request.form['primary_id'])
            transaction.settled = "1"
            date_settled = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
            transaction.date_settled = date_settled                  
            DB.session.commit()
        if 'comment_add' in request.form:
            x = transactions.query.get(request.form['transaction_id'])
            print(request.form['transaction_id'])
            print(x)
            x.comments = x.comments + ',' + request.form['submitting_user'] + ' ' + request.form['comment']
            DB.session.commit()
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username)) 

    to_list = transactions.query.filter_by(from_user=query).all()
    from_list = transactions.query.filter_by(to_user=query).all()

    return render_template('else_profile.html', username=username, query=query, query_user=query_user, from_list=from_list, to_list=to_list, message=message)


@app_blueprint.route('/<username>/friends', methods = ['GET', 'POST'])
def friends_display(username, message=None):
    user = users.query.filter_by(username=username).first() 
    x = []
    friend_list = []
    url_list = []
    x = friends.query.filter_by(username=username).first()
    friend_list = x.friend.split(',')
    for y in friend_list:
        if y != '':
            z = users.query.filter_by(username=y).first()
            url_list.append(z)
    if request.method == 'POST':    
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'add_transaction' in request.form:
            if request.form['from_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['from_user']).first()
                friend_list = x.friend.split(',')
                if request.form['to_user'] not in friend_list:
                    message = request.form['to_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')                                        
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            elif request.form['to_user'] == username:
                friend_list = []
                x = friends.query.filter_by(username=request.form['to_user']).first()
                friend_list = x.friend.split(',')
                if request.form['from_user'] not in friend_list:
                    message = request.form['from_user'] + " is not a friend"
                else:
                    date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')                                        
                    transaction = transactions(from_user=request.form['from_user'], to_user=request.form['to_user'], amount=request.form['amount'], settled="0", date_created=date_created)
                    DB.session.add(transaction)
                    DB.session.commit()
            else:
                message = "You can only add your own transactions"
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))
        if 'group_submission' in request.form:
            group_name = request.form['group_name']
            group_members = request.form['people_in_group']
            group = groups(name=group_name, group_members=group_members)
            DB.session.add(group)
            DB.session.commit()
            return redirect(url_for('app_blueprint.group_page', username=username, group_name=group_name))

    return render_template('friends.html', username=username, user=user, friend_list=url_list, message=message)


@app_blueprint.route('/<username>/groups', methods = ['GET', 'POST'])
def groups_display(username):
    user = users.query.filter_by(username=username).first() 
    group_list = []
    groups_all = groups.query.all()
    for group in groups_all:
        #print(group.group_members)
        print(username)
        if username in group.group_members.split(','):
            print(group.group_members)
            group_list.append(group)
    if request.method == 'POST':    
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))

    return render_template('all_groups.html', username=username, user=user, group_list=group_list)            


@app_blueprint.route('/<username>/groups/<group_name>', methods = ['GET', 'POST'])
def group_page(username, group_name):
    group = groups.query.filter_by(group_name=group_name).first()
    members_list = []
    url_list = []
    members_list = group.group_members.split(',')
    for m in members_list:
        if m != '':
            z = users.query.filter_by(username=m).first()
            url_list.append(z) 
    if request.method == 'POST':
        if 'search' in request.form:
            return redirect(url_for('app_blueprint.search_results', username=username, query=request.form['search_name']))
        if 'logout' in request.form:
            return redirect(url_for('app_blueprint.sign_up'))
        if 'log' in request.form:
            return redirect(url_for('app_blueprint.log', username=username))
        if 'friends' in request.form:
            return redirect(url_for('app_blueprint.friends_display', username=username))
        if 'groups' in request.form:
            return redirect(url_for('app_blueprint.groups_display', username=username))
        if 'add_transaction' in request.form:
            date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
            print (group_name)
            transaction = group_transactions(group_name=group_name, from_member=request.form['from_member'], to_member=request.form['to_member'], amount=request.form['amount'], settled="0", date_created=date_created)
            print(transaction)
            DB.session.add(transaction)
            DB.session.commit()
        if 'settle' in request.form:
            transaction = group_transactions.query.get(request.form['primary_id'])
            transaction.settled = "1"
            date_settled = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
            transaction.date_settled = date_settled                  
            DB.session.commit()

    transaction_list = group_transactions.query.filter_by(group_name=group_name).all()

    return render_template('group_page.html', username=username, group_name=group_name, group_members=group.group_members, members_list=url_list, transaction_list=transaction_list)