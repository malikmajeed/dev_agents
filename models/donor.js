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
    // Virtual field for convenience
    fullName: {
      type: DataTypes.VIRTUAL,
      get() {
        return `${this.firstName} ${this.lastName}`;
      },
      set() {
        throw new Error('Do not try to set the `fullName` value directly.');
      },
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

export default Donor;
