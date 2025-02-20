![R (2)](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/a064577c-9302-4f43-b3bf-3d4f84245a6f)
نام پروژه :  تانل های wangyu و proxyforwarder
---------------------------------------------------------------
----------------------------------
![check](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/13de8d36-dcfe-498b-9d99-440049c0cf14)
**امکانات و نکات**

- تانل های wangyu اعم از tinyvpn و udpspeed و udp2raw و tinymapper
- پورت فوروارد proxyforwarder
- ترکیب tinyvpn با تانل و پورت فورواردرها
- قابلیت ویرایش تانل و پورت فوروارد
- دارای ریست تایمر
- دارای status و restart برای تانل ها
- پشتیبانی از 5 کلاینت ( tinyvpn فعلا در حال حاضر از یک کلاینت پشتیبانی میکند)
- پشتیبانی از udp
- دو پورت فوروارد tinymapper و proxyforwarder از tcp هم پشتیبانی میکند
-------

**توضیحات**
- اگر روش tinyvpn برای شما کار نکرد سرور خارج خود را عوض کنید و اطمینان یابید که سرور ایران شما محدودیتی ندارد در غیر این صورت باید از ترکیب geneve با تانل های wangyu بهره ببرید
- ممکن است tinyvpn با udp2raw ترکیبش برای بعضی از کانفیگ ها کار نکند که میتوانید نخست با tinyvpn ایپی بسازید و سپس از udpspeeder استفاده نمایید
- برای تانل udp2raw با udpspeeder و سایر موارد میتوانید از این پروزه استفاده نمایید https://github.com/Azumi67/UDP2RAW_FEC
- برای لوکال تانل ها هم که اسکریپت روبرو میتواند به شما کمک کند https://github.com/Azumi67/6TO4-GRE-IPIP-SIT
- در بعضی از روش ها از مقدار کلاینت یه حای مقدار پورت هم میتوان استفاده کرد. به طور مثال اگر من 3 تا پورت دارم میتوانم تعداد کلاینت هم عدد 3 را وارد کنم. 

---------

![6348248](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/398f8b07-65be-472e-9821-631f7b70f783)
**آموزش نصب با اسکریپت**
 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/Azumi67/Rathole_reverseTunnel/assets/119934376/fcbbdc62-2de5-48aa-bbdd-e323e96a62b5" alt="Image"> </strong>نصب tinyvpn</summary>

------------------------------------ 

<p align="right">
  <img src="https://github.com/user-attachments/assets/acd06ba1-de2f-4feb-a8ae-65c549143029" alt="Image" />
  </p>

- بین سرور و کلاینت یک پرایوت ایپی ایجاد میکنیم و از این پرایوت ایپی در تانل ها و پورت فوروارد ها استفاده مینماییم
- نخست سرور را کانفیگ میکنم. پورت تانل را 4040 میذارم و ساب نت را 10.22.22.1 انتخاب میکنم. شما میتوانید اعداد دیگری بگذارید
- نام tun را آزومی میذارم و fec را فعال میکنم. پس yes را وارد میکنم
- برای mode عدد 1 و برای timeout عدد 1 را قرار میدهم
- مقدار mtu را 1250 قرار میدهم که باعث قطعی نشود. این مورد را باید خود شما بررسی کنید اما به صورت معمول باید بر روی 1250 جواب دهد
- پسورد را ازومی قرار میدهم
- ریست تایمر را فعال نمیکنم. شما بسته به نیاز خودتان میتوانید فعال کنید
- یک keepalive هم ایجاد میشود

**کلاینت**
<p align="right">
  <img src="https://github.com/user-attachments/assets/d55241fd-f37f-4db9-973e-128f828a19bf" alt="Image" />
  </p>

- حالا در کلاینت ایپی پابلیک ورژن 4 سرور خارج را وارد میکنم و سپس پرایوت ایپی را وارد میکنم . 10.22.22.2
- مانند سرور fec را فعال میکنم و پورت تانل هم 4040 وارد میکنم
- نام tun را ازومی وارد میکنم و مقادیر timeout و mode را بر روی 1 قرار میدهم
- مقدار mtu را 1250 قرار میدهم و پسورد را ازومی وارد میکنم
- حالا میتوانیم از این ایپی برای تانل و موارد دیگر استفاده نماییم

------------------

  </details>
</div>  

 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/Azumi67/Rathole_reverseTunnel/assets/119934376/fcbbdc62-2de5-48aa-bbdd-e323e96a62b5" alt="Image"> </strong>نصب tinyvpn و udp2raw</summary>

------------------------------------ 

<p align="right">

  <img src="https://github.com/user-attachments/assets/c1a5f791-8ca7-48e2-9ff1-fc56bf9eeff4" alt="Image" />
  </p>

- مانند قبل نحست باید tinyvpn کانفیگ شود و سپس udp2raw . باید در نظر داشت که این مورد ممکن است برای تمام کانفیگ ها و سرور جوابگو نباشد و باید خود شما ان را تست نمایید
- مانند قبل پورت tinyvp و ساب نت و نام tun و فعال کردن fec را وارد میکنم و مقدار timeout و mode را یک قرار میدهم و مقدار mtu را 1250 و پسورد را ازومی وارد میکنم
- من تنها یک پورت کانفیگ دارم پس عدد 1 را برای تعداد پورت وارد میکنم
- پورت تانل برای udp2raw را 4040 وارد میکنم و پورت udp که پورت کانفیک است را 18743 وارد میکنم و پسورد هم وارد میکنم
- برای raw mode از udp استفاده میکنم

<p align="right">

  <img src="https://github.com/user-attachments/assets/8b70e50e-f58d-47da-b5ef-8e1c141d147d" alt="Image" />
  </p>

- مانند قبل در کلاینت، نخست کانفیگ tinyvpn را انجام میدهم. پابلیک ایپی 4 سرور خارج را وارد میکنم.
- ساب نت را انتخاب میکنم. پرایوت ایپی، ایپی مقابل سرور خارج خواهد بود
- گزینه fec را فعال میکنم و مقدار timeout و mode را یک قرار میدهم
- نام tun و پسورد را ازومی قرار میدهم. پورت tinyvpn همانند سرور خارج خواهد بود
- مقدار mtu را 1250 میذارم
- حالا برای کانفیگ udp2raw مانند قبل انجام میدم
- پورت udp که همان پورت کانفیگ است را 18743 قرار میدهم. پورت تانل مانند سرور خارج 4040 قرار میدهم
- پرایوت ایپی ادرسی که با tinyvp به دست اوردم را در اینجا قرار میدهم. باید پرایوت ایپی سرور خارج را در اینجا وارد نمایید
- پسورد را مانند سرور خارج وارد میکنم و raw mode را udp انتخاب میکنم

------------------

  </details>
</div>  

 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/Azumi67/Rathole_reverseTunnel/assets/119934376/fcbbdc62-2de5-48aa-bbdd-e323e96a62b5" alt="Image"> </strong>نصب tinyvpn و proxyforwarder</summary>

------------------------------------ 


<p align="right">

  <img src="https://github.com/user-attachments/assets/d5c699a9-4a66-4cc2-932a-0d2a8dbe9fe6" alt="Image" />
  </p>

- در سرور خارج تنها کافی است که tinyvpn نصب شود و پورت فوواردر تنها کافی است که در کلاینت ایران نصب شود
- مانند قبل کانفیگ tinyvpn را انجام میدهم
- پورت tinyvpn را 4040 قرار میدهم. ساب نت را 10.22.22.1 انتخاب میکنم
- نام tun و پسورد را ازومی وارد میکنم
- گزینه fec را فعال میکنم و مقدار timeout و mode را 1 وارد میکنم
- مقدار mtu هم 1250 وارد میکنم که مشکلات قطعی برطرف شود
<p align="right">

  <img src="https://github.com/user-attachments/assets/a16f08d3-ab41-4fd7-bf97-ecd63fed1e73" alt="Image" />
  </p>

- حالا کلاینت را کانفیگ میکنم. ایپی پابلیک سرور خارج را وارد میکنم و پرایوت ایپی مقابل سرور خارج را وارد میکنم کخ میشود 10.22.22.2
- گزینه fec را فعال میکنم و پورت tinyvpn را 4040 قرار میدهم
- مانند سرور خارج پسورد و نام tun را ازومی قرار میدهم
- مقدار timeout و mode را یک قرار میدهم و مقدار mtu را 1250 وارد میکنم
<p align="right">

  <img src="https://github.com/user-attachments/assets/9824cf42-9128-4d86-b47e-e7d5ef7bccc0" alt="Image" />
  </p>
  
- حالا بین tcp و udp، udp را انتخاب میکنم و تعداد پورت را یک قرار میدهم
- حالا نوبت کانفیگ یک میباشد
- پورت لوکال که مانند پورت کانفیگ 18743 وارد میکنم
- ادرس destination همان ایپی پرایوت سرور خارج 10.22.22.1 میشود
- پورت destination هم که پورت گانفیگ میباشد که همان 18743 میباشد
- بقیه مقادیر را به صورت دیفالت قرار میدهم
<p align="right">

  <img src="https://github.com/user-attachments/assets/2be94401-d105-4e80-9913-ecd41253a873" alt="Image" />
  </p>
  

- برای ویرایش هم میتوانید هم source address و هم source destination را ویرایش کنید یا بلاک جدیدی اضافه کنید یا حتی پاک کنید . بعد از ویرایش یا اضافه کردن حتما گزینه save را بزنید

-------------------------

  </details>
</div>  

 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/Azumi67/Rathole_reverseTunnel/assets/119934376/fcbbdc62-2de5-48aa-bbdd-e323e96a62b5" alt="Image"> </strong>نصب tinyvpn و tinymapper</summary>

------------------------------------ 

<p align="right">

  <img src="https://github.com/user-attachments/assets/d5c699a9-4a66-4cc2-932a-0d2a8dbe9fe6" alt="Image" />
  </p>

- در سرور خارج تنها کافی است که tinyvpn نصب شود و پورت فوواردر تنها کافی است که در کلاینت ایران نصب شود
- مانند قبل کانفیگ tinyvpn را انجام میدهم
- پورت tinyvpn را 4040 قرار میدهم. ساب نت را 10.22.22.1 انتخاب میکنم
- نام tun و پسورد را ازومی وارد میکنم
- گزینه fec را فعال میکنم و مقدار timeout و mode را 1 وارد میکنم
- مقدار mtu هم 1250 وارد میکنم که مشکلات قطعی برطرف شود
<p align="right">

  <img src="https://github.com/user-attachments/assets/a16f08d3-ab41-4fd7-bf97-ecd63fed1e73" alt="Image" />
  </p>

- حالا کلاینت را کانفیگ میکنم. ایپی پابلیک سرور خارج را وارد میکنم و پرایوت ایپی مقابل سرور خارج را وارد میکنم کخ میشود 10.22.22.2
- گزینه fec را فعال میکنم و پورت tinyvpn را 4040 قرار میدهم
- مانند سرور خارج پسورد و نام tun را ازومی قرار میدهم
- مقدار timeout و mode را یک قرار میدهم و مقدار mtu را 1250 وارد میکنم
<p align="right">

  <img src="https://github.com/user-attachments/assets/5dee9dd7-2c96-4a50-9aff-3746cb51902b" alt="Image" />
  </p>

- کانفیگ tinymapper را اغاز میکنم. تنها یک پورت دارم پس عدد یک را وارد میکنم
- ایپی ورژن 4 را وارد میکنم چون پرایوت ایپی tinyvpn ورژن 4 میباشد
- لوکال ادرس که همیشه 0.0.0.0 میباشد
- پورت لوکال هماند پورت کانفیگ قرار میدهم یعنی 18743
- ریموت ادرس را همان پرایوت ایپی که با tinyvpn در سرور ساخته ایم، قرار میدهم یعنی 10.22.22.1
- پورت ریموت را 18743 قرار میدهم
- چون میخواهم کانفیگ udp استفاده کنم قسمت پروتکل را udp انتخاب میکنم
- پورت فوروارد ها حتما نیار به لوکال ایپی یا پرایوت ایپی tinyvpn دارند تا به درستی کار کنند
<p align="right">

  <img src="https://github.com/user-attachments/assets/8c65df08-eda7-475c-a0dd-3e47ba6e8c47" alt="Image" />
  </p>

- برای ویرایش ان هم میتوانید مانند اسکرین مقابل عمل کنید
------------------

  </details>
</div>  

 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/Azumi67/Rathole_reverseTunnel/assets/119934376/fcbbdc62-2de5-48aa-bbdd-e323e96a62b5" alt="Image"> </strong>نصب udpspeeder</summary>

------------------------------------ 

<p align="right">

  <img src="https://github.com/user-attachments/assets/b44366ac-375e-4440-b54b-bddf1b9bc256" alt="Image" />
  </p>

- نصب udpspeeder را از سرور خارج اغاز میکنم.من تنها یک کلاینت دارم و کانفیگ کلاینت یک را اغاز میکنم. پورت تانل را 4040 قرار میدهم و پورت udp را 18743 وارد میکنم
- پسورد ار ازومی وارد میکنم و گزینه fec را فعال میکنم
- مقدار mode را یک قرار میدهم
<p align="right">

  <img src="https://github.com/user-attachments/assets/5b77b06f-fe6f-4e71-818b-9a917ec6a5c4" alt="Image" />
  </p>

- پورت تانل 4040 را وارد میکنم
- پورت udp را 18743 وارد میکنم
- پسورد را ازومی وارد میکنم
- ایپی ادرس سرور خارج را وارد میکنم
- مقدار mode را یک وارد میکنم
- گزینه fec را فعال میکنم

------------------

  </details>
</div>  
