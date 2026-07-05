import { sequelize, DataTypes } from '../lib/db.js';

// Define the Donor model
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
    totalDonated: {
      type: DataTypes.DECIMAL(12, 2),
      allowNull: false,
      defaultValue: 0,
    },
  },
  {
    tableName: 'donors',
    timestamps: true,
    underscored: true,
  }
);

// Associations – will be called from the central model index after all models are loaded
Donor.associate = (models) => {
  if (models.Donation) {
    Donor.hasMany(models.Donation, {
      foreignKey: 'donor_id',
      as: 'donations',
    });
  }
};

export default Donor;
