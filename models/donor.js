import { DataTypes } from 'sequelize';
import { sequelize } from '../lib/db.js';

// Donor model definition
// Represents an individual donor who can make many donations.
// Fields are kept minimal for the MVP; additional profile data can be added later.
const Donor = sequelize.define(
  'Donor',
  {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true,
    },
    firstName: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    lastName: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    email: {
      type: DataTypes.STRING,
      allowNull: false,
      unique: true,
      validate: {
        isEmail: true,
      },
    },
    phone: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    address: {
      type: DataTypes.TEXT,
      allowNull: true,
    },
    // Store bcrypt hashed password for authentication
    passwordHash: {
      type: DataTypes.STRING,
      allowNull: false,
    },
  },
  {
    tableName: 'donors',
    timestamps: true,
    underscored: true,
  }
);

// Associations – defined in a separate init step to avoid circular imports.
// The Donation model (not shown here) will reference donorId.
Donor.associate = (models) => {
  if (models.Donation) {
    Donor.hasMany(models.Donation, {
      foreignKey: 'donor_id',
      as: 'donations',
    });
  }
};

export default Donor;
