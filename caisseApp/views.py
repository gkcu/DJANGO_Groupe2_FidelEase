from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as loginAuth
from django.contrib import messages
from .models import Product, AppUser, Code, Gift, Message, Transaction, Facture
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as logoutAuth
from .forms import ProductForm, GiftForm
from django.db.models import Q


def login(request):
    if(request.method=="GET"):
        return render(request, 'login.html')
    elif (request.method=="POST"):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        print(user)
        if user is not None:
            loginAuth(request, user)
            messages.success(request, 'Login successful.')
            return redirect('products') 
        else:
            messages.error(request, 'Invalid login credentials.')
            print("invalid credentials")
            return redirect('login')
    else :
        return render(request, 'login.html')
    

def logout(request):
    logoutAuth(request)
    return redirect('login') 

#@login_required(login_url='login')
def products(request):
    allProducts = Product.objects.all()
    context={'product_list':allProducts}
    return render(request,'products.html',context)

#@login_required(login_url='login')
def productDetails(request,id):
    p = Product.objects.get(pk=id)
    if p is not None:
        context={'product':p}
        return render(request,'productDetails.html',context)
    else : 
        messages.error("Product not found.")
   
#@login_required(login_url='login')
def addProduct(request):
    if request.method == "POST":
        print("inside post")
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('products')
    else:
        print("inside get")
        form = ProductForm()
    
    return render(request, 'addProduct.html', {'form': form})    
    
#@login_required(login_url='login')
def editProduct(request, id):
    product = Product.objects.get(pk=id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('products')  
    else:
        form = ProductForm(instance=product)

    return render(request, 'editProduct.html', {'form': form})
    
#@login_required(login_url='login')
def deleteProduct(request,id):
    if(request.method=="GET"):
        p = Product.objects.get(pk=id)
        context={"product":p}
        return render(request,'deleteProduct.html',context)
    elif(request.method=="POST"):
        if(Product.objects.get(pk=id).delete()):
            return redirect("products")
    else:
        messages.error(request,"Failed to delete the product.")
       
#@login_required(login_url='login')
def caisse(request):
    products = Product.objects.all()  # Load all products to display in the form
    if request.method == "POST":
        userId = request.POST.get("userId")
        # Retrieve user
        try:
            user = AppUser.objects.get(pk=userId)
        except AppUser.DoesNotExist:
            messages.error(request, 'AppUser does not exist!')
            return render(request, 'caisse.html', {'products': products})

        total = 0
        fac = Facture(userId=user)
        fac.save()  
        for product in products:
            if str(product.id) in request.POST.getlist('products'):
                quantity = int(request.POST.get(f"quantity_{product.id}", 1))
                total += product.price * quantity
                transaction = Transaction(productId=product, quantity=quantity)
                transaction.save()
                fac.transactionIds.add(transaction)
        points = total // 50
        user.points += points
        user.save()

        return redirect("facture", fac.id)  # Redirect to a view that shows the facture

    return render(request, 'caisse.html', {'products': products})

#@login_required(login_url='login')
def facture(request, id):
    facture = Facture.objects.get(pk=id)
    transactions = facture.transactionIds.all()
    total_cost = sum(t.productId.price * t.quantity for t in transactions)

    context = {
        'facture': facture,
        'transactions': transactions,
        'total_cost': total_cost,
    }
    return render(request, 'facture.html', context)
        
#@login_required(login_url='login')
def scanGiftCode(request):
    gift = None
    if request.method == 'POST':
        gift_code = request.POST.get('giftCode')
        try:
            code = Code.objects.get(pk=gift_code)
            gift = code.giftId
        except Code.DoesNotExist:
            pass
    return render(request, 'scanGiftCode.html', {'gift': gift})           
                    
#@login_required(login_url='login')
def gifts(request):
    gifts = Gift.objects.all()
    return render(request, 'gifts.html', {'gifts': gifts})

#@login_required(login_url='login')
def addGift(request):
    if request.method == 'POST':
        form = GiftForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gifts')
    else:
        form = GiftForm()
    return render(request, 'addGift.html', {'form': form})

#@login_required(login_url='login')
def editGift(request,id):
    gift = Gift.objects.get(pk=id)
    if request.method == 'POST':
        form = GiftForm(request.POST, instance=gift)
        if form.is_valid():
            form.save()
            return redirect('gifts')
    else:
        form = GiftForm(instance=gift)
        
    return render(request, 'editGift.html', {'form': form})

#@login_required(login_url='login')        
def deleteGift(request,id):
    if(request.method=="GET"):
        g = Gift.objects.get(pk=id)
        context={"gift":g}
        return render(request,'deleteGift.html',context)
    elif(request.method=="POST"):
        if(Gift.objects.get(pk=id).delete()):
            return redirect("gifts")
    else:
        messages.error(request,"Failed to delete the Gift.")

#@login_required(login_url='login')
def history(request):
    factures = Facture.objects.all().select_related('userId').order_by('-date')
    return render(request, 'history.html', {'factures': factures})
    
#@login_required(login_url='login')
def inbox(request):
    messages = Message.objects.all().order_by('-date').select_related('fromUserId', 'toUserId')
    return render(request, 'inbox.html', {'messages': messages})

#@login_required(login_url='login')
def sendMessage(request, user_id):
    admin_id = request.user.id
    user = AppUser.objects.get(pk=user_id)
    # Fetch messages between the admin and the selected user
    messages = Message.objects.filter(
        (Q(fromUserId=admin_id) & Q(toUserId=user_id)) | 
        (Q(fromUserId=user_id) & Q(toUserId=admin_id))
    ).order_by('date')
    return render(request, 'sendMessage.html', {'messages': messages, 'user': user})
    