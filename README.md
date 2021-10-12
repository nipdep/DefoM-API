# DefoM-API
backend API for the deforestation application


## Project prograse following table
| UserCase | Dev | status |
| :---     | :---| :---   |
| User registration | @Thushan97, @nipdep | completed, completed |
| User Log-in and Log out | @Thushan97, @Dilaxsaswaran , @nipdep | completed, running, completed |
| User Detail updates | @Thushan97, @Dilaxsaswaran | todo, todo |
| Forest registration | @Thushan97, @nipdep | completed, completed |
| Forest detailt update | @Thushan97, @nipdep | todo, todo |
| forest tile seperation and update | @nipdep | completed |
| daily forest tile satellite feed invoking and store | @nipdep | completed |
| daily threat type prediction on latest tiles | @nipdep | completed |
| daily forest threar type updates accourding to predictions | @nipdep | completed |
| entire forest satellite view invoking and store | @nipdep | completed |
| predict and save tile threat area on changes | @nipdep | completed |
| get threat results in to rendered map | @Thushan97, @nipdep | todo, todo |
| create forum message thread by Citizen | @Dilaxsaswaran, @Thushan97 | running, todo |
| view massage only by allowed parties | @Dilaxsaswaran, @Thushan97 | running, todo |
| set restriction on thread access | @Dilaxsaswaran, @Thushan97 | todo, todo |
| put message and read message | @Dilaxsaswaran, @Thushan97 | running, todo |
| add comments to messages | @Dilaxsaswaran, @Thushan97 | running, todo |
| pin location and forest in messages | @Dilaxsaswaran, @nipdep, @Thushan97 | todo, todo, todo |
| deleted or close thread | @Dilaxsaswaran, @Thushan97 | todo, todo |

* * *
## Unittesting
you have to first create clone of a MongoDB Atlas cloud servers Local instance:
```
mongodump --uri="mongodb+srv://defomAdmin:<password>@defomdb.osisk.mongodb.net" --db defom --out dump_defom | mongorestore dump_defom
```
*make sure you have installed [MongoDB ToolKit](https://docs.mongodb.com/database-tools/installation/installation-windows/) before run the above command.
