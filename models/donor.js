import { DataTypes, Model } from 'sequelize';
import sequelize from '../lib/db.js';

class Donor extends Model {}

Donor.init(
  {
    id: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      primaryKey: true,
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
      validate: { isEmail: true },
    },
    passwordHash: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    phone: {
      type: DataTypes.STRING,
      allowNull: true,
    },
    address: {
      type: DataTypes.TEXT,
      allowNull: true,
    },
  },
  {
    sequelize,
    modelName: 'Donor',
    tableName: 'donors',
    timestamps: true,
    underscored: true,
  }
);

// Define associations – will be called from the central model index after all models are loaded
Donor.associate = (models) => {
  Donor.hasMany(models.Donation, {
    foreignKey: 'donor_id',
    as: 'donations',
  });
};

export default Donor;
