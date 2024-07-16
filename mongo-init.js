db.createUser({
    user: 'admin',
    pwd: 'admin',
    roles: [
      {
        role: 'readWrite',
        db: 'mongo',
      },
    ],
  });

// sleep(1000);

// rs.initiate({
// _id: "rs0",
// members: [
//     { _id: 0, host: "mongodb:27017" }
// ]
// });