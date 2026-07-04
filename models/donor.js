import { DataTypes, Model } from 'sequelize';
import db from '../lib/db.js';
import bcrypt from 'bcryptjs';

class Donor extends Model {
  /**
   * Verify a plain text password against the stored hash.
   * @param {string} password
   * @returns {Promise<boolean>}
   */
  async verifyPassword(password) {
    if (!this.passwordHash) return false;
    return bcrypt.compare(password, this.passwordHash);
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
    // Virtual field for raw password input; not persisted.
    password: {
      type: DataTypes.VIRTUAL,
      set(value) {
        this.setDataValue('password', value);
      },
    },
    passwordHash: {
      type: DataTypes.STRING,
    },
    phone: {
      type: DataTypes.STRING,
    },
    address: {
      type: DataTypes.TEXT,
    },
  },
  {
    sequelize: db,
    modelName: 'Donor',
    tableName: 'donors',
    timestamps: true,
    hooks: {
      /**
       * Hash password before creating a donor record.
       */
      beforeCreate: async (donor) => {
        if (donor.password) {
          donor.passwordHash = await bcrypt.hash(donor.password, 10);
        }
      },
      /**
       * Hash password before updating a donor record if password was changed.
       */
      beforeUpdate: async (donor) => {
        if (donor.password) {
          donor.passwordHash = await bcrypt.hash(donor.password, 10);
        }
      },
    },
  }
);

export default Donor;
