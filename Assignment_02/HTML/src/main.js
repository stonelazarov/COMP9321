//login
$('#loginSubmit').click(()=>{
    let url = 'http://127.0.0.1:5000/auth/login'
    let data = {
        username: $('#usernameInput').val(),
        password: $('#passwordInput').val()
    }
    fetch(url,{
        method:'POST',
        body:JSON.stringify(data),
        headers:{
            "Content-Type":"application/json"
        }
    })
    .then(res=>{
        if(res.status === 400 || res.status === 403) {
            document.getElementById("usernameInput").disabled=true;
            document.getElementById("passwordInput").disabled=true;
            document.getElementById("sumbit").disabled=true;
            return false;
        }
        return res.json()
    })
    .then(resp=>{
        console.log(resp.token)
        var moiveData = {}
        moiveData.Suburb = document.getElementById('title').value;
        moiveData.Rooms = document.getElementById('genres').value;
        moiveData.Type = document.getElementById('homepage').value;
        moiveData.Distance = document.getElementById('overview').value;
        moiveData.Car = document.getElementById('poster_path').value;
        moiveData.Building_Area = document.getElementById('production_companies').value;
        moiveData.Year = document.getElementById('popularity').value;
        moiveData.Year = document.getElementById('id').value;
        console.log(moiveData)
        getMoive(moiveData)
    })
    .catch(err=>{
        console.log(err)
    })
})

//
function getMoive(data) {
    var url = 'http://127.0.0.1:5000/house/data';
    fetch(url, {
        method: "POST", // *GET, POST, PUT, DELETE, etc.
        mode: "cors", // no-cors, cors, *same-origin
        body: JSON.stringify(data), // data can be `string` or {object}!
        cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
        headers: {
            "Content-Type": "application/json; charset=utf-8",
            "AUTH-TOKEN": window.localStorage.getItem("AUTH-TOKEN")
            // "Content-Type": "application/x-www-form-urlencoded",
        }
    })
    .then(res => res.json())
    .then(response => {
          console.log(response)
            var Moive = document.getElementById('result')
            if(response.moiveid){
                Moive.innerText = `$ ${response.moiveid} K`
                document.getElementById('access_num').innerText=response.access

                if(!$('#invalidResult').hasClass('d-none')) $('#invalidResult').addClass('d-none')
                $('#result').removeClass('d-none')
            }
            else {
                if(!$('#result').hasClass('d-none')) $('#result').addClass('d-none')
                document.getElementById('getMoiveError').innerText=response.message
                $('#invalidResult').removeClass('d-none')
                $('#getMoiveError').text(response.message)
            }
        console.log('Success:', JSON.stringify(response))
    })
    .catch(error => console.error('Error:', error))
}