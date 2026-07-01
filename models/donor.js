import { DataTypes, Model } from 'sequelize';
import sequelize from '../lib/db.js';
import bcrypt from 'bcryptjs';

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
    // Virtual field for raw password input; not persisted
    password: {
      type: DataTypes.VIRTUAL,
      allowNull: false,
    },
    passwordHash: {
      type: DataTypes.STRING,
      allowNull: false,
    },
    createdAt: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
    },
    updatedAt: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW,
    },
  },
  {
    sequelize,
    modelName: 'Donor',
    tableName: 'donors',
    timestamps: true,
    hooks: {
      beforeCreate: async (donor) => {
        if (donor.password) {
          donor.passwordHash = await bcrypt.hash(donor.password, 10);
        }
      },
      beforeUpdate: async (donor) => {
        if (donor.password) {
          donor.passwordHash = await bcrypt.hash(donor.password, 10);
        }
      },
    },
  }
);

export default Donor;
