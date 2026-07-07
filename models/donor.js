import { DataTypes, Model } from 'sequelize';
import db from '../lib/db.js';
import bcrypt from 'bcryptjs';

class Donor extends Model {
  /**
   * Compare a plain text password with the stored hashed password.
   * @param {string} password
   * @returns {Promise<boolean>}
   */
  async validPassword(password) {
    return bcrypt.compare(password, this.password);
  }
}

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
    password: {
      type: DataTypes.STRING,
      allowNull: false,
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
    sequelize: db,
    modelName: 'Donor',
    tableName: 'donors',
    timestamps: true,
    hooks: {
      beforeCreate: async (donor) => {
        if (donor.password) {
          const salt = await bcrypt.genSalt(10);
          donor.password = await bcrypt.hash(donor.password, salt);
        }
      },
      beforeUpdate: async (donor) => {
        if (donor.changed('password')) {
          const salt = await bcrypt.genSalt(10);
          donor.password = await bcrypt.hash(donor.password, salt);
        }
      },
    },
  }
);

export default Donor;
